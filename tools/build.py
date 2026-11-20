"""Önálló index.html készítése a page.html-ből (az artifact forrásából).

Futtatás (a projektmappából):  python -I tools/build.py

A page.html artifactnak készül, ezért nincs benne <!doctype>/<head>/<body>.
Ez a szkript köré teszi a teljes HTML-keretet, és beágyazza a stores.json-t,
így az index.html dupla kattintással (file://) is megnyitható.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
page = open(os.path.join(ROOT, "page.html"), encoding="utf-8").read()
stores = json.load(open(os.path.join(ROOT, "stores.json"), encoding="utf-8"))

title = re.search(r"<title>(.*?)</title>", page)
title = title.group(1) if title else "Tiszta Kosár"
body = re.sub(r"<title>.*?</title>\s*", "", page, count=1)
inline = "<script>window.__STORES__=" + json.dumps(stores, ensure_ascii=False).replace("</", "<\\/") + ";</script>"

html = f"""<!doctype html>
<html lang="hu">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]:not([hidden=until-found i]){{display:none!important}}</style>
{inline}
</head>
<body>
{body.strip()}
</body>
</html>
"""
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8", newline="\n").write(html)
print("kész: index.html", len(html), "bájt")
