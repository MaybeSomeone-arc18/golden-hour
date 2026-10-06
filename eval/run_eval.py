"""Measure how often a local Gemma writes a sentence whose numbers all match the facts.
usage: python eval/run_eval.py MODEL.gguf label  (20 cities x walk lengths 30, 60, 120 min = 60 sentences)"""
import json, sys, time, statistics, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from datetime import datetime, timezone, timedelta
from golden_hour.__main__ import fetch
from golden_hour.scorer import parse, best_window
from golden_hour.nudge import make, valid
from llama_cpp import Llama
CITIES = json.load(open(os.path.join(os.path.dirname(__file__), "cities.json")))
llm = Llama(model_path=sys.argv[1], n_ctx=1024, n_threads=2, verbose=False)
rows = []
for name, lat, lon in CITIES:
    api = fetch(lat, lon)
    now = (datetime.now(timezone.utc) + timedelta(seconds=api["utc_offset_seconds"])).strftime("%Y-%m-%dT%H:%M")
    for minutes in (30, 60, 120):
        f = best_window(parse(api), now, minutes); f["day"] = "today" if f["start"][:10] == now[:10] else "tomorrow"
        t = time.time(); text, src = make(f, name, llm); dt = time.time() - t
        raw = getattr(make, "last_raw", None) if f["score"] >= 60 else None
        kind = "gemma" if src == "gemma" else ("no_good_window" if f["score"] < 60 else "rejected")
        make.last_raw = None
        rows.append({"city": name, "minutes": minutes, "src": src, "kind": kind, "secs": round(dt, 2), "text": text, "rejected_raw": raw if kind == "rejected" else None, "facts": f})
        print(name, minutes, src, round(dt, 1), flush=True)
import collections
n = len(rows); kinds = collections.Counter(r["kind"] for r in rows)
summary = {"model": sys.argv[2], "n": n, "gemma_valid": kinds["gemma"], "rejected_by_validator": kinds["rejected"],
           "no_good_window_model_skipped": kinds["no_good_window"],
           "median_secs": round(statistics.median(r["secs"] for r in rows if r["kind"] != "no_good_window"), 2),
           "min_secs": min(r["secs"] for r in rows if r["kind"] != "no_good_window"), "max_secs": max(r["secs"] for r in rows if r["kind"] != "no_good_window")}
print(json.dumps(summary))
json.dump({"summary": summary, "rows": rows}, open(os.path.join(os.path.dirname(__file__), f"results_{sys.argv[2]}.json"), "w"), indent=1)
