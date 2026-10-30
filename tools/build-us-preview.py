#!/usr/bin/env python3
"""
Make a GitHub Pages preview of us-site/ (served at https://greyleads5.github.io/GreyLeads/).

    python3 tools/build-us-site.py && python3 tools/build-us-preview.py [out_dir]

GitHub Pages serves a project site under /GreyLeads/, so root links are rewritten,
page links get .html, Google Analytics is switched off and every page is noindex.
"""
import os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "us-site")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "us-preview")
BASE = "/GreyLeads"

shutil.rmtree(OUT, ignore_errors=True)
shutil.copytree(SRC, OUT, ignore=shutil.ignore_patterns("wrangler.jsonc", "_headers", "_redirects", ".assetsignore"))

pages = set()
for d, _, fs in os.walk(OUT):
    for f in fs:
        if f.endswith(".html"):
            rel = os.path.relpath(os.path.join(d, f), OUT)[:-5]
            pages.add("/" + rel)
pages.discard("/index")


def fix_url(u):
    path, sep, rest = re.match(r"([^#?]*)([#?]?)(.*)", u).groups()
    if path == "/" or path == "":
        path = "/"
    elif path.rstrip("/") in pages:
        path = path.rstrip("/") + ".html"
    return BASE + path + sep + rest


for d, _, fs in os.walk(OUT):
    for f in fs:
        if not f.endswith(".html"):
            continue
        p = os.path.join(d, f)
        s = open(p, encoding="utf-8").read()
        s = re.sub(r'((?:href|src|poster|action)=")(/(?!/)[^"]*)"', lambda m: m.group(1) + fix_url(m.group(2)) + '"', s)
        s = re.sub(r'srcset="([^"]*)"', lambda m: 'srcset="' + re.sub(r'(^|,\s*)/(?!/)', lambda n: n.group(1) + BASE + "/", m.group(1)) + '"', s)
        s = re.sub(r"(url\(['\"]?)/assets/", r"\1" + BASE + "/assets/", s)
        s = re.sub(r"(['\"])/assets/", r"\1" + BASE + "/assets/", s)
        s = s.replace('location.pathname!=="/"&&location.pathname!=="/index.html"',
                      'location.pathname!=="' + BASE + '/"&&location.pathname!=="' + BASE + '/index.html"')
        s = s.replace('history.replaceState(null,"","/")', 'history.replaceState(null,"","' + BASE + '/")')
        s = s.replace("gtag('config','G-YSTJKSS88D')", "void 0")
        s = re.sub(r'<meta name="robots" content="[^"]*">', '<meta name="robots" content="noindex, nofollow">', s)
        if 'name="robots"' not in s:
            s = s.replace("<head>", '<head>\n<meta name="robots" content="noindex, nofollow">', 1)
        open(p, "w", encoding="utf-8").write(s)

open(os.path.join(OUT, "robots.txt"), "w").write("User-agent: *\nDisallow: /\n")
open(os.path.join(OUT, ".nojekyll"), "w").write("")
print(f"Preview built in {OUT} ({len(pages) + 1} pages), base {BASE}/")
