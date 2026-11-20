"""Boltadatok frissítése a Tiszta Kosárhoz.

Futtatás (a projektmappából):  python -I tools/refresh_stores.py
Bemenet:  data/stores-map.json   (termék -> cashmap/kifli azonosítók, seed linkek)
Kimenet:  stores.json            (a weboldal ezt tölti be)
          data/cashmap-catalog.json (a seed-oldalakról begyűjtött teljes alkategória-lista, azonosító-kereséshez)

Szabályok:
- Csak nyilvános termékoldalakat kér le (GET), bejelentkezés nélkül.
- Ha egy bolt korábban szerepelt, de most már nem aktív / eltűnt: "gone" állapot, dátummal.
- Ha egy forrás most nem érhető el (hálózati hiba), a korábbi adat marad, nem írjuk felül.
"""
import json, os, re, subprocess, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, "data", "stores-map.json")
OUT = os.path.join(ROOT, "stores.json")
CAT = os.path.join(ROOT, "data", "cashmap-catalog.json")
TODAY = datetime.date.today().isoformat()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
sys.stdout.reconfigure(encoding="utf-8")

# cashmap bolt -> egységes lánc-név
CHAIN = [
    (r"tesco", "Tesco"), (r"spar|interspar", "Spar"), (r"lidl", "Lidl"), (r"aldi", "Aldi"),
    (r"penny", "Penny"), (r"auchan", "Auchan"), (r"kifli", "Kifli"), (r"cba|pr[ií]ma", "CBA"),
    (r"coop", "Coop"), (r"metro", "Metro"), (r"re[aá]l", "Reál"), (r"dm\b", "dm"), (r"rossmann", "Rossmann"),
]

def chain_of(name):
    n = (name or "").lower()
    for pat, ch in CHAIN:
        if re.search(pat, n): return ch
    return None

def get(url):
    r = subprocess.run(["curl.exe", "-s", "-L", "--ssl-no-revoke", "-A", UA, "-w", "\n%{http_code}", url], capture_output=True)
    body = r.stdout.decode("utf-8", "replace")
    body, _, code = body.rpartition("\n")
    return int(code or 0), body

def cashmap_product(pid):
    code, html = get(f"https://cashmap.hu/termekek/{pid}/x")
    if code != 200: return code, None
    i = html.find("product = {")
    if i < 0: return code, None
    p, _ = json.JSONDecoder().raw_decode(html[i + len("product = "):])
    return code, p

def kifli_status(pid):
    code, body = get(f"https://www.kifli.hu/api/v1/products/{pid}")
    if code == 404: return "gone"
    if code != 200: return None
    try:
        d = json.loads(body)
    except Exception:
        return None
    if d.get("archived"): return "gone"
    code, body = get(f"https://www.kifli.hu/api/v1/products/{pid}/stock")
    if code != 200: return None
    try:
        s = json.loads(body)
    except Exception:
        return None
    return "active" if not s.get("unavailabilityReason") else "unavailable"

def main():
    cfg = json.load(open(MAP, encoding="utf-8"))
    old = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {"products": {}}
    catalog = json.load(open(CAT, encoding="utf-8")) if os.path.exists(CAT) else {}

    # 1) seed-oldalak: alkategória-listák a katalógusba
    for url in cfg.get("seeds", []):
        m = re.search(r"/termekek/(\d+)", url)
        if not m: continue
        code, p = cashmap_product(int(m.group(1)))
        if not p: print("seed hiba", url, code); continue
        for a in [p] + (p.get("alternative_products") or []):
            catalog[str(a["id"])] = {"name": a["name"], "brand": (a.get("brand") or {}).get("name"),
                                     "shops": sorted({chain_of(s.get("display_name") or s.get("name")) for s in a.get("active_shops") or []} - {None}),
                                     "seen": TODAY}
    json.dump(catalog, open(CAT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 2) termékenkénti boltállapot
    result = {"updated": TODAY, "products": {}}
    for name, src in cfg["products"].items():
        prev = {s["store"]: s for s in old.get("products", {}).get(name, {}).get("stores", [])}
        now, sources_ok = {}, True
        for pid in src.get("cashmap", []):
            code, p = cashmap_product(pid)
            if p is None:
                if code == 404: continue
                sources_ok = False; continue
            for s in p.get("active_shops") or []:
                ch = chain_of(s.get("display_name") or s.get("name"))
                if not ch: continue
                st = "active" if s.get("status", "active") == "active" else "gone"
                if now.get(ch, {}).get("status") != "active":
                    now[ch] = {"store": ch, "status": st, "checked": TODAY, "source": "cashmap"}
        for pid in src.get("kifli", []):
            st = kifli_status(pid)
            if st is None: sources_ok = False; continue
            if now.get("Kifli", {}).get("status") != "active":
                now["Kifli"] = {"store": "Kifli", "status": "active" if st == "active" else ("unavailable" if st == "unavailable" else "gone"),
                                "checked": TODAY, "source": "kifli"}
        # korábban látott, most hiányzó bolt -> kivezetve (csak ha minden forrás válaszolt)
        for ch, s in prev.items():
            if ch in now: continue
            if sources_ok and s.get("status") != "gone":
                now[ch] = {**s, "status": "gone", "checked": TODAY, "goneSince": TODAY}
            else:
                now[ch] = s
        for ch, s in now.items():
            if s["status"] == "active":
                s["lastSeen"] = TODAY
                s.pop("goneSince", None)
            elif ch in prev and prev[ch].get("lastSeen"):
                s.setdefault("lastSeen", prev[ch]["lastSeen"])
        result["products"][name] = {"stores": sorted(now.values(), key=lambda s: s["store"])}
        print(f"{name}: " + ", ".join(f"{s['store']}({s['status']})" for s in result["products"][name]["stores"]))
    json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("kész:", OUT)

if __name__ == "__main__":
    main()
