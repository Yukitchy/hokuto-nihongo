#!/usr/bin/env python3.11
"""One-time: turn ai/index.html (data-i18n keyed, inline I dict) into works/ai-wo-torimodose.json."""
import json, re, pathlib
from bs4 import BeautifulSoup, NavigableString

ROOT = pathlib.Path(__file__).resolve().parent.parent
html = (ROOT / "ai" / "index.html").read_text()
soup = BeautifulSoup(html, "html.parser")
# inline I dict: const I={ en:{}, ja:{...}, zh:{...} };  -> quote keys, single-quoted JS strings -> JSON
raw = re.search(r"const I=(\{.*?\n\}\});", html, re.S).group(1)
raw = re.sub(r"(?m)^(en|ja|zh):", r'"\1":', raw)
def js2json(s):
    out, i, q = [], 0, None
    while i < len(s):
        c = s[i]
        if q is None:
            if c == "'": q = "'"; out.append('"')
            elif c == '"': q = '"'; out.append('"')
            else: out.append(c)
        else:
            if c == "\\": out.append(s[i:i+2] if s[i+1] != "'" else "'"); i += 2; continue
            if c == q: q = None; out.append('"')
            elif c == '"' and q == "'": out.append('\\"')
            else: out.append(c)
        i += 1
    return "".join(out)
I = json.loads(js2json(raw))

def inner(el): return "".join(str(c) for c in el.contents).strip()
def T(el, attr=None):
    k = el.get("data-i18n") if attr is None else el.get("data-i18n-ph")
    en = inner(el) if attr is None else el.get(attr)
    return {"en": en, "ja": I["ja"].get(k, en), "zh": I["zh"].get(k, en)}
def ex_li(li):
    m = li.find("span", class_="m"); b = li.find("button", class_="spk"); say = b["data-say"] if b else ""
    mt = T(m) if m else {"en": "", "ja": "", "zh": ""}
    if m: m.decompose()
    if b: b.decompose()
    return {"jp": inner(li), "m": mt, "say": say}
def drill_li(li):
    m = li.find("span", class_="m"); mt = T(m) if m else {"en": "", "ja": "", "zh": ""}
    if m: m.decompose()
    for b in li.find_all("button", class_="blank"): b.replace_with(NavigableString("{{blank:" + b.get_text(strip=True) + "}}"))
    return {"jp": inner(li), "m": mt}

hero = soup.select_one(".hero"); h1 = hero.find("h1"); en = h1.find("span", class_="en"); h1_en = T(en); en.decompose()
d = {
 "slug": "ai-wo-torimodose", "kind": "song", "root": False,
 "langs": [{"code": "en", "label": "EN"}, {"code": "ja", "label": "日本語"}, {"code": "zh", "label": "中文"}],
 "html_lang": {"en": "en", "ja": "ja", "zh": "zh-Hant"}, "tts_lang": "ja-JP",
 "brand": "北斗<b>×</b>日本語", "brand_href": "../../",
 "title_tag": soup.title.get_text(), "description": soup.find("meta", attrs={"name": "description"})["content"],
 "video": re.search(r"videoId:'([\w-]+)'", html).group(1),
 "nav": {"back": T(soup.select_one('[data-i18n="nav.back"]')), "back_href": "../../", "quiz": T(soup.select_one('[data-i18n="nav.quiz"]')),
         "segs": [{"href": a["href"], "label": inner(a)} for a in soup.select("#nav a") if not a.get("data-i18n")]},
 "hero": {"eyebrow": T(hero.select_one(".eyebrow")), "h1": inner(h1), "h1_en": h1_en, "lead": T(hero.select_one(".lead")),
          "howto": [{"t": T(x.select_one(".t")), "d": T(x.select_one(".d"))} for x in hero.select(".howto > div")]},
 "ui": {k: T(soup.select_one(f'[data-i18n="{k2}"]')) for k, k2 in [("all", "btn.all"), ("slow", "btn.slow"), ("loop", "btn.loop"), ("loopline", "btn.loopline"), ("rec", "btn.rec"), ("readmine", "btn.readmine"), ("word", "th.word"), ("meaning", "th.meaning"), ("drill", "drill.h")]},
 "lyrics": {"h": T(soup.select_one('[data-i18n="ly.h"]')), "p": T(soup.select_one('[data-i18n="ly.p"]')),
            "links": [{"href": a["href"], "text": (T(a) if a.get("data-i18n") else {"en": inner(a), "ja": inner(a), "zh": inner(a)}), "dark": "dark" in a["class"]} for a in soup.select(".lyrics a")]},
 "title_line": {"jp": inner(soup.select_one(".title-line .jp")), "en": T(soup.select_one(".title-line .en")),
                "say": soup.select_one(".title-line .act-say")["data-say"], "seg": [float(x) for x in soup.select_one(".title-line .act-seg")["data-seg"].split(",")]},
 "segments": [], "quiz": [], "homework": {}, "cheat": {}, "footer": [T(s) for s in soup.select("footer span")],
 "quiz_head": {"h2": T(soup.select_one('[data-i18n="quiz.h"]')), "who": T(soup.select_one('[data-i18n="quiz.sub"]'))},
 "score_perfect": " — 愛をとりもどせ!!",
}
for s in soup.select(".seg"):
    tbl = s.find("table"); rows = [[inner(tr.find_all("td")[0]), T(tr.find_all("td")[1])] for tr in tbl.select("tr")[1:]]
    ta = s.find("textarea"); yt = s.select_one(".yourturn")
    d["segments"].append({
      "id": s["id"], "h": T(s.select_one(".head h2")), "time": inner(s.select_one(".head .t")),
      "seg": [float(x) for x in s.select_one(".ctl")["data-seg"].split(",")],
      "cue": T(s.select_one(".cue")), "words": rows,
      "gp": [T(g) for g in s.select(".gp")], "examples": [ex_li(li) for li in s.select(".ex li")],
      "drill_h": T(s.select_one(".drill h3")), "drill": [drill_li(li) for li in s.select(".drill ol > li")],
      "yourturn": {"label": T(yt.find("label")), "ph": T(ta, "placeholder"), "store": ta["data-store"]},
    })
# quiz: JS objects with {en,ja,zh} per field
qsrc = re.search(r"const QUIZ=\[(.*?)\n\];", html, re.S).group(1)
qjson = json.loads("[" + js2json(re.sub(r"(?<=[{,])(\w+):", r'"\1":', qsrc)) + "]")
d["quiz"] = [{"q": q["q"], "o": [{l: q["o"][l][i] for l in q["o"]} for i in range(len(q["o"]["en"]))], "a": q["a"], "why": q["why"]} for q in qjson]
g2 = soup.select("#quiz .grid2 > div")
d["homework"] = {"h": T(g2[0].find("h3")), "list": [T(li) for li in g2[0].select("li")]}
d["cheat"] = {"h": T(g2[1].find("h3")), "rows": [[inner(tr.find_all("td")[0]), T(tr.find_all("td")[1])] for tr in g2[1].select("tr")]}
out = ROOT / "works" / "ai-wo-torimodose.json"; out.write_text(json.dumps(d, ensure_ascii=False, indent=1))
print("wrote", out, "segments:", len(d["segments"]), "quiz:", len(d["quiz"]))
