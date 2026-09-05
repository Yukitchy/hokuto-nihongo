#!/usr/bin/env python3.11
"""One-time: turn the hand-written index.html (+ i18n.js) into works/hokuto.json.
Every translatable string becomes {"en":..,"ja":..,"zh":..} (a "T"); build.py assigns data-i18n keys by JSON path."""
import json, re, pathlib
from bs4 import BeautifulSoup, NavigableString

ROOT = pathlib.Path(__file__).resolve().parent.parent
html = (ROOT / "index.html").read_text()
soup = BeautifulSoup(html, "html.parser")
I18N = json.loads(re.sub(r"(?m)^(ja|zh): \{", r'"\1": {', re.search(r"window\.I18N\s*=\s*(\{.*\});?\s*$", (ROOT / "i18n.js").read_text(), re.S).group(1)))

def inner(el):  # innerHTML trimmed
    return "".join(str(c) for c in el.contents).strip()

def T(en):
    en = en.strip()
    return {"en": en, "ja": I18N["ja"].get(en, en), "zh": I18N["zh"].get(en, en)}

def ex_li(li):
    """example <li>: jp html + <span class=m> + <button class=spk data-say>"""
    m = li.find("span", class_="m"); b = li.find("button", class_="spk")
    say = b["data-say"] if b else ""
    if m: m_text = inner(m); m.decompose()
    else: m_text = ""
    if b: b.decompose()
    return {"jp": inner(li), "m": T(m_text), "say": say}

def drill_li(li):
    m = li.find("span", class_="m"); m_text = inner(m) if m else ""
    if m: m.decompose()
    for b in li.find_all("button", class_="blank"):
        b.replace_with(NavigableString("{{blank:" + b.get_text(strip=True) + "}}"))
    return {"jp": inner(li), "m": T(m_text)}

VIDS = dict(re.findall(r"(yt\w+):'([\w-]+)'", re.search(r"const VIDS=\{([^}]+)\}", html).group(1)))

hero = soup.select_one(".hero")
h1 = hero.find("h1"); en_span = h1.find("span", class_="en"); en_txt = inner(en_span); en_span.decompose()
data = {
  "slug": "hokuto", "lang_default": "en",
  "brand": "北斗<b>×</b>日本語",
  "title_tag": "北斗の拳で日本語 — Learn Japanese with Fist of the North Star",
  "description": soup.find("meta", attrs={"name": "description"})["content"],
  "hero": {
    "eyebrow": T(inner(hero.select_one(".eyebrow"))),
    "h1": inner(h1), "h1_en": T(en_txt),
    "lead": T(inner(hero.select_one(".lead"))),
    "meta": [T(inner(s)) for s in hero.select(".meta span")],
    "howto": [{"t": T(inner(d.select_one(".t"))), "d": T(inner(d.select_one(".d")))} for d in hero.select(".howto > div")],
  },
  "nav": {"warmup": T("Warm-up"), "quiz": T("Quiz"), "song": T("♪ Song"), "song_href": "ai/"},
  "warmup": {},
  "lines": [], "quiz": [], "homework": [], "cheat": [], "footer": []
}
# ---- warm-up ----
w = soup.select_one("#warmup")
h2 = w.select_one(".sec-head h2"); tag = h2.find("span", class_="tag"); tag_txt = inner(tag); tag.decompose()
data["warmup"] = {
  "h2": T(inner(h2)), "tag": T(tag_txt), "who": T(inner(w.select_one(".who"))),
  "chips": [{"jp": inner(c.select_one(".j")), "e": T(inner(c.select_one(".e"))), "say": c.select_one(".spk")["data-say"]} for c in w.select(".chip")],
  "cols": []
}
for col in w.select(".grid2 > div"):
    c = {"h": T(inner(col.find("h3"))), "p": T(inner(col.find("p"))), "examples": [ex_li(li) for li in col.select(".ex li")]}
    a = col.select_one("a.btn")
    if a: c["button"] = {"text": T(inner(a)), "href": a["href"]}
    if col.select_one(".panel"): c["video"] = VIDS["ytOP"]
    data["warmup"]["cols"].append(c)
# ---- lines ----
for sec in soup.select("section.lesson"):
    h2 = sec.select_one(".sec-head h2"); tag = h2.find("span", class_="tag"); tag_txt, tag_cls = inner(tag), [x for x in tag["class"] if x != "tag"][0]; tag.decompose()
    ctl = sec.select_one(".ctl"); pid = ctl["data-player"]
    bub = sec.select_one(".bubble")
    cols = sec.select(".grid2 > div")
    words_tbl = cols[0].find("table")
    head = [T(inner(th)) for th in words_tbl.select("tr:first-child th")]
    rows = []
    for tr in words_tbl.select("tr")[1:]:
        cells = tr.find_all("td")
        rows.append([inner(cells[0])] + [T(inner(c)) for c in cells[1:]])
    g = cols[1]
    grammar = {"h": T(inner(g.find("h3"))), "gp": [T(inner(x)) for x in g.select(".gp")],
               "p": T(inner(g.find("p"))) if g.find("p") else None,
               "examples": [ex_li(li) for li in g.select(".ex li")],
               "note": T(inner(g.select_one(".note"))) if g.select_one(".note") else None}
    words_note = cols[0].select_one(".note")
    drill = sec.select_one(".drill"); yt = drill.select_one(".yourturn"); ta = yt.find("textarea")
    data["lines"].append({
      "id": sec["id"], "num": sec.select_one(".sec-head .num").get_text(strip=True),
      "title": inner(h2), "tag": {"cls": tag_cls, "text": T(tag_txt)}, "who": T(inner(sec.select_one(".who"))),
      "line": {"jp": inner(bub.select_one(".jp")), "romaji": inner(bub.select_one(".romaji")), "en": T(inner(bub.select_one(".en"))),
               "say": ctl.select_one(".act-say")["data-say"]},
      "clip": {"video": VIDS[pid], "scene": [float(x) for x in ctl["data-scene"].split(",")], "line": [float(x) for x in ctl["data-line"].split(",")],
               "src": T(inner(ctl.select_one(".src")))},
      "words": {"h": T(inner(cols[0].find("h3"))), "head": head, "rows": rows, "note": T(inner(words_note)) if words_note else None},
      "grammar": grammar,
      "drill": {"h": T(inner(drill.find("h3"))), "items": [drill_li(li) for li in drill.select("ol > li")]},
      "yourturn": {"label": T(inner(yt.find("label"))), "ph": T(ta["placeholder"]), "store": ta["data-store"], "hint": T(inner(yt.select_one(".hint")))},
      "done": T(inner(drill.select_one(".done label")).replace('<input type="checkbox" class="doneBox">', "").strip()),
    })
# ---- quiz (from JS) ----
qjs = re.search(r"const QUIZ=\[(.*?)\n\];", html, re.S).group(1)
for m in re.finditer(r"\{q:'(.*?)',o:\[(.*?)\],a:(\d),why:'(.*?)'\}", qjs):
    q, opts, a, why = m.groups()
    opts = re.findall(r"'((?:[^'\\]|\\.)*)'", opts)
    un = lambda s: s.replace("\\'", "'")
    data["quiz"].append({"q": T(un(q)), "o": [T(un(o)) for o in opts], "a": int(a), "why": T(un(why))})
qz = soup.select_one("#quiz")
qh2 = qz.select_one(".sec-head h2")
data["quiz_head"] = {"h2": T(inner(qh2)), "who": T(inner(qz.select_one(".who")))}
g2 = qz.select(".grid2 > div")
data["homework"] = {"h": T(inner(g2[0].find("h3"))), "items": [T(inner(li)) for li in g2[0].select("li")]}
data["cheat"] = {"h": T(inner(g2[1].find("h3"))), "rows": [[inner(tr.find_all("td")[0]), T(inner(tr.find_all("td")[1]))] for tr in g2[1].select("tr")]}
data["footer"] = [T(inner(s)) for s in soup.select("footer span")]
data["score_msgs"] = {"perfect": " — 一片の悔いなし！", "good": " — 退かぬ！", "bad": " — お前はもう…"}
data["toggles"] = {"ruby": T("あ Furigana <span class=\"k\">on</span>"), "romaji": T("Aa Romaji <span class=\"k\">on</span>")}
out = ROOT / "works" / "hokuto.json"; out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(data, ensure_ascii=False, indent=1))
missing = [k for k in re.findall(r'"en": "([^"]+)", "ja": "\1"', out.read_text())]
print("wrote", out, "lines:", len(data["lines"]), "quiz:", len(data["quiz"]), "untranslated(en==ja):", len(missing))
for k in missing[:15]: print("  ", k[:70])
