#!/usr/bin/env python3.11
"""Build lesson pages from works/*.json.
  python3.11 build.py hokuto      -> index.html (root work)     python3.11 build.py <slug> -> works/<slug>/index.html
A work JSON has "kind": "lines" or "song". Any {"en":..,"ja":..,"zh":..} object is translatable ("T");
the page shows the first language in "langs" (base) and switches to the others by the JSON path key."""
import json, re, sys, pathlib, copy
from jinja2 import Environment, FileSystemLoader

ROOT = pathlib.Path(__file__).resolve().parent
env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=False)
env.filters["blanks"] = lambda s: re.sub(r"\{\{blank:(.*?)\}\}", r'<button class="blank">\1</button>', s)

def is_T(x): return isinstance(x, dict) and "en" in x and set(x) <= {"en", "ja", "zh"}

def walk(node, path, i18n, langs):
    """Give every T a key (JSON path) and a .base text; collect per-language dicts."""
    if is_T(node):
        base = langs[0]
        node["k"] = path; node["base"] = node.get(base) or node["en"]
        for l in langs[1:]:
            v = node.get(l)
            if v and v != node["base"]: i18n.setdefault(l, {})[path] = v
        return
    if isinstance(node, dict):
        for k, v in list(node.items()): walk(v, f"{path}.{k}" if path else k, i18n, langs)
    elif isinstance(node, list):
        for i, v in enumerate(node): walk(v, f"{path}.{i}", i18n, langs)

def build(slug):
    d = copy.deepcopy(json.loads((ROOT / "works" / f"{slug}.json").read_text()))
    langs = [x["code"] for x in d["langs"]]
    i18n = {l: {} for l in langs[1:]}
    # quiz is rendered by JS per language -> plain {code:text} maps
    quiz = [{"q": {l: q["q"].get(l) or q["q"]["en"] for l in langs},
             "o": [{l: o.get(l) or o["en"] for l in langs} for o in q["o"]],
             "a": q["a"], "why": {l: q["why"].get(l) or q["why"]["en"] for l in langs}} for q in d["quiz"]]
    walk(d, "", i18n, langs)
    out_dir = ROOT if d.get("root") else ROOT / "works" / slug
    base = "" if d.get("root") else "../../"
    ctx = dict(d=d, quiz=quiz, i18n=i18n, base=base)
    if d["kind"] == "lines":
        vids = {f"yt{L['num']}": L["clip"]["video"] for L in d["lines"]}
        op = next((c["video"] for c in d["warmup"]["cols"] if c.get("video")), None)
        if op: vids["ytOP"] = op
        ctx["vids"] = vids
    html = env.get_template(f"{d['kind']}.html.j2").render(**ctx)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html)
    print(f"built {slug} -> {out_dir.relative_to(ROOT) if out_dir != ROOT else '.'}/index.html ({len(html)//1024} KB, i18n: {[len(v) for v in i18n.values()]})")

if __name__ == "__main__":
    args = sys.argv[1:]
    for s in (args or [p.stem for p in sorted((ROOT / 'works').glob('*.json'))]): build(s)
