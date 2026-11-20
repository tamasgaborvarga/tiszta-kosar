# Tiszta Kosár

Címkeolvasó a polc előtt: mit tegyél a kosárba, és mit hagyj a polcon. Tejtermékek (egyelőre joghurt) ajánlott és kerülendő besorolása az összetevőlista és a tápérték alapján, kereséssel, szűrőkkel, változatcsaládokkal és összehasonlítással.

## Felépítés

- `index.html` — az egész oldal (CSS, termékadat a `P` tömbben, JS). Claude-artifactként publikálva, ezért nincs benne `<!doctype>`/`<head>`/`<body>` keret; önálló hostoláshoz ezt köré kell tenni.
- `img/` — termékfotók (520 px, webp); `img/shoppy/` a második körben bekerült termékeké.
- `stores.json` — boltadatok (lánc, állapot, utolsó ellenőrzés), az oldal tölti be.
- `tools/refresh_stores.py` — boltadat-frissítés: `python -I tools/refresh_stores.py` a projektmappából.
- `data/stores-map.json` — termék → forrásazonosítók a frissítőhöz; `data/cashmap-catalog.json` — alkategória-katalógus.

## Új kategória

`CATS` tömbbe egy sor, a `P`-be `cat:"<id>"` sorok, és ha kell, egy `data-cat="<id>"` útmutató-blokk.
