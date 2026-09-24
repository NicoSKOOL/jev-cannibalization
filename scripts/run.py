#!/usr/bin/env python3
"""Find searches where Google splits impressions between two or more of your
pages, and ask Jev which page should own each one.

Usage:
  python run.py gsc.json --domain example.com [--max-cost 1.0]

gsc.json / gsc.csv: Search Console rows with query, page, clicks, impressions,
position (query x page, e.g. the last 90 days). A Windsor.ai export
({"result": [...]}) works as-is.

Output: ./jev-cannibalization/<domain>/out/cannibalization.html
"""
import argparse
import collections
import csv
import hashlib
import json
import os
import random
import re
import statistics
import sys
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from dashboard import render  # noqa: E402

# ── the rulebook: Jev's probabilities in, outcomes out. Change and re-run for free.
MIN_QUERY_IMPR = 15   # the search must matter a little
MIN_PAGE_IMPR = 3     # each competing page must really be shown
MAX_PAGES = 3         # a choice between 3 pages keeps Jev's state small
MIN_OWNER_CONF = 0.70 # below this Jev is guessing which page should win
SPLIT_INTENT = 0.60   # same page wins, but the others really are rivals
MIN_FIX_CONF = 0.70   # Jev's suggested fix is only acted on above this

URL = "https://openrouter.ai/api/alpha/decisions"
UA = {"User-Agent": "Mozilla/5.0 (compatible; jev-cannibalization/1.0)"}
EST_COST_PER_CALL = 0.00005   # measured: 64 decisions cost $0.0027


def load_keys(workdir):
    for f in (workdir / ".env", Path.home() / ".config/jev-seo/.env",
              Path.home() / ".config/jev-internal-links/.env"):
        if f.exists():
            for line in f.read_text().splitlines():
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def load_rows(path):
    p = Path(path)
    if p.suffix.lower() == ".csv":
        with p.open(newline="", encoding="utf-8-sig") as f:
            raw = list(csv.DictReader(f))
    else:
        d = json.loads(p.read_text())
        raw = d["result"] if isinstance(d, dict) else d
    rows = []
    for r in raw:
        r = {k.strip().lower(): v for k, v in r.items()}
        q, page = r.get("query") or r.get("top queries"), r.get("page") or r.get("url")
        if not q or not page:
            continue
        rows.append({"query": q, "page": page,
                     "clicks": int(float(r.get("clicks") or 0)),
                     "impressions": int(float(r.get("impressions") or 0)),
                     "position": float(r.get("position") or 0)})
    if not rows:
        sys.exit("No rows with both a query and a page. Export query x page data, not queries alone.")
    return rows


def path(u):
    p = urlparse(u)
    return (p.path or "/") + (f"?{p.query}" if p.query else "")


def candidates(rows):
    by = collections.defaultdict(list)
    for r in rows:
        if r["impressions"] >= MIN_PAGE_IMPR:
            by[r["query"]].append(r)
    out = []
    for q, v in by.items():
        v = sorted(v, key=lambda r: -r["impressions"])[:MAX_PAGES]
        total = sum(r["impressions"] for r in v)
        if len(v) >= 2 and total >= MIN_QUERY_IMPR:
            out.append({"query": q, "impressions": total, "clicks": sum(r["clicks"] for r in v),
                        "pages": [{"url": r["page"], "impressions": r["impressions"],
                                   "clicks": r["clicks"], "position": round(r["position"], 1)}
                                  for r in v]})
    return sorted(out, key=lambda c: -c["impressions"])


def snapshot(url):
    try:
        r = requests.get(url, headers=UA, timeout=25)
        soup = BeautifulSoup(r.text, "lxml")
    except Exception as e:
        return {"url": url, "error": str(e)}
    for bad in soup(["script", "style", "noscript", "nav", "footer", "header"]):
        bad.decompose()
    md = soup.find("meta", attrs={"name": "description"})
    main = soup.find("main") or soup.body or soup
    paras = [p.get_text(" ", strip=True) for p in main.find_all("p")]
    paras = [p for p in paras if len(p) > 60][:2]
    return {"url": url, "status": r.status_code,
            "title": soup.title.get_text(strip=True) if soup.title else "",
            "h1": soup.h1.get_text(" ", strip=True) if soup.h1 else "",
            "description": md.get("content", "").strip() if md else "",
            "intro": re.sub(r"\s+", " ", " ".join(paras))[:500]}


def build_state(c, snaps):
    lines = [f'SEARCH QUERY: "{c["query"]}"', "", "OUR PAGES THAT GOOGLE SHOWS FOR THIS QUERY:"]
    for n, p in enumerate(c["pages"], 1):
        s = snaps.get(p["url"], {})
        lines += [f"PAGE {n}: {path(p['url'])}", f"  Title: {s.get('title', '')}",
                  f"  H1: {s.get('h1', '')}", f"  Description: {s.get('description', '')}",
                  f"  Opening text: {s.get('intro', '')[:350]}", ""]
    return "\n".join(lines)


def build_questions(c):
    pages = {str(n): path(p["url"])[:120] for n, p in enumerate(c["pages"], 1)}
    return {
        "owner": {"type": "choice", "criteria": pages,
                  "instructions": "Which ONE of our pages best gives this searcher what they want?"},
        "same_intent": {"type": "noul", "instructions": (
            "These pages compete for the same need: a searcher typing this "
            "query would be equally happy landing on any of them.")},
        "fix": {"type": "choice",
                "instructions": "What should the site owner do about these pages for this query?",
                "criteria": {
                    "leave": "Nothing. The pages serve genuinely different needs, overlap is harmless",
                    "strengthen": "Keep all pages, but point internal links and on-page focus for this query at the best page",
                    "differentiate": "Keep all pages, but retarget the weaker page to a clearly different angle",
                    "merge": "Merge the weaker page into the best page and redirect it"}},
        "intent": {"type": "choice", "instructions": "What does this searcher want?",
                   "criteria": {"brand": "A specific business or website by name",
                                "browse": "To browse products, listings or options",
                                "learn": "Information or advice",
                                "local": "A local provider or service to contact"}},
    }


class Jev:
    def __init__(self, cache):
        self.cache, self.lock = cache, threading.Lock()
        self.model = os.environ.get("JEV_MODEL", "~typesafe/jev-latest")
        self.stats = {"calls": 0, "cached": 0, "cost": 0.0, "in_tok": 0, "errors": 0}

    def decide(self, state, questions, attempt=0):
        body = {"model": self.model, "state": state, "questions": questions}
        h = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:20]
        hit = self.cache / f"{h}.json"
        if hit.exists():
            with self.lock:
                self.stats["cached"] += 1
                d = json.loads(hit.read_text())
                self.stats["cost"] += (d.get("usage") or {}).get("cost", 0) or 0
                self.stats["in_tok"] += (d.get("usage") or {}).get("input_tokens", 0) or 0
            return d
        t0 = time.time()
        try:
            r = requests.post(URL, json=body, timeout=60,
                              headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"})
            if r.status_code in (429, 500, 502, 503) and attempt < 5:
                time.sleep(2 ** attempt + random.random())
                return self.decide(state, questions, attempt + 1)
            r.raise_for_status()
            d = r.json()
        except Exception as e:
            with self.lock:
                self.stats["errors"] += 1
            return {"error": str(e)}
        d["_ms"] = round((time.time() - t0) * 1000)
        hit.write_text(json.dumps(d))
        with self.lock:
            u = d.get("usage") or {}
            self.stats["calls"] += 1
            self.stats["cost"] += u.get("cost", 0) or 0
            self.stats["in_tok"] += u.get("input_tokens", 0) or 0
        return d


def outcomes(cands, jev):
    items, clusters = [], {}
    for c in cands:
        j = c.get("jev")
        if not j:
            continue
        o = int(j["owner"]["choice"]) - 1
        oc, si = j["owner"]["confidence"], j["same_intent"]["noul"]
        out = ("unsure" if oc < MIN_OWNER_CONF else "wrong" if o != 0
               else "split" if si >= SPLIT_INTENT else "fine")
        row = {"q": c["query"], "impr": c["impressions"], "clicks": c["clicks"],
               "pages": [{"p": path(p["url"]), "impr": p["impressions"], "pos": p["position"],
                          "prob": j["owner"]["probabilities"].get(str(n), 0)}
                         for n, p in enumerate(c["pages"], 1)],
               "owner": o, "ownerConf": oc, "same": si, "fix": j["fix"]["choice"],
               "fixConf": j["fix"]["confidence"], "intent": j["intent"]["choice"],
               "out": out, "ms": c.get("jev_ms") or 0, "state": c["state"]}
        items.append(row)
        if out == "wrong":
            k = (row["pages"][0]["p"], row["pages"][o]["p"])
            cl = clusters.setdefault(k, {"google": k[0], "jev": k[1], "impr": 0, "queries": []})
            cl["impr"] += row["impr"]
            cl["queries"].append({"q": row["q"], "impr": row["impr"], "gpos": row["pages"][0]["pos"],
                                  "jpos": row["pages"][o]["pos"], "conf": oc})
    counts = collections.Counter(r["out"] for r in items)
    return {
        "items": items, "counts": counts,
        "clusters": sorted(clusters.values(), key=lambda c: -c["impr"]),
        "stats": {"n": len(items), "cost": jev.stats["cost"], "tokens": jev.stats["in_tok"],
                  "model": jev.model,
                  "p50": statistics.median([r["ms"] for r in items if r["ms"]] or [0]),
                  "fixActed": sum(r["fixConf"] >= MIN_FIX_CONF for r in items),
                  "wrongImpr": sum(r["impr"] for r in items if r["out"] == "wrong")},
        "rules": {"owner": MIN_OWNER_CONF, "split": SPLIT_INTENT, "fix": MIN_FIX_CONF},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gsc", help="query x page export, .json (Windsor) or .csv")
    ap.add_argument("--domain", required=True)
    ap.add_argument("--days", default="90 days", help="label for the period, e.g. '90 days'")
    ap.add_argument("--max-cost", type=float, default=1.0)
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    domain = re.sub(r"/.*$", "", re.sub(r"^www\.", "", re.sub(r"^https?://", "", args.domain.strip())))
    work = Path.cwd() / "jev-cannibalization" / domain
    for d in ("data", "cache", "out"):
        (work / d).mkdir(parents=True, exist_ok=True)
    load_keys(work)
    if not os.environ.get("OPENROUTER_API_KEY"):
        sys.exit("No OPENROUTER_API_KEY. Put it in ~/.config/jev-seo/.env (see README).")

    cands = candidates(load_rows(args.gsc))
    if not cands:
        sys.exit("No searches where 2+ of your pages each got impressions. Nothing to judge.")
    est = len(cands) * EST_COST_PER_CALL
    print(f"{len(cands)} searches with real overlap. Estimated Jev cost: ${est:.4f}")
    if est > args.max_cost:
        sys.exit(f"Over --max-cost ${args.max_cost}. Raise it to continue.")

    snap_file = work / "data" / "pages.json"
    snaps = json.loads(snap_file.read_text()) if snap_file.exists() else {}
    todo = sorted({p["url"] for c in cands for p in c["pages"]} - set(snaps))
    print(f"reading {len(todo)} pages")
    with ThreadPoolExecutor(8) as ex:
        for s in ex.map(snapshot, todo):
            snaps[s["url"]] = s
    snap_file.write_text(json.dumps(snaps, indent=1, ensure_ascii=False))

    jev = Jev(work / "cache")
    for c in cands:
        c["state"] = build_state(c, snaps)
    with ThreadPoolExecutor(10) as ex:
        resps = list(ex.map(lambda c: jev.decide(c["state"], build_questions(c)), cands))
    for c, r in zip(cands, resps):
        c["jev"], c["jev_ms"] = r.get("answers"), r.get("_ms")
        if not c["jev"]:
            c["error"] = r.get("error") or str(r)[:300]
    (work / "data" / "judgements.json").write_text(json.dumps(cands, indent=1, ensure_ascii=False))

    a = outcomes(cands, jev)
    a["days"] = args.days
    report = work / "out" / "cannibalization.html"
    report.write_text(render(a, domain))
    st = jev.stats
    print(f"Jev: {st['calls']} new calls, {st['cached']} cached, {st['errors']} errors, ${st['cost']:.4f}")
    print(f"outcomes: {dict(a['counts'])}")
    print(f"report: {report}")
    if not args.no_open:
        webbrowser.open(report.as_uri())


if __name__ == "__main__":
    main()
