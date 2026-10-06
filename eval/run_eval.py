"""Measure how often a local Gemma writes a sentence whose numbers all match the facts.
usage: python eval/run_eval.py MODEL.gguf label"""
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
    f = best_window(parse(api), now, 60); f["day"] = "today" if f["start"][:10] == now[:10] else "tomorrow"
    t = time.time(); text, src = make(f, name, llm); dt = time.time() - t
    rows.append({"city": name, "src": src, "secs": round(dt, 2), "text": text, "facts": f})
    print(name, src, round(dt, 1), flush=True)
n = len(rows); g = sum(r["src"] == "gemma" for r in rows)
summary = {"model": sys.argv[2], "n": n, "gemma_valid": g, "fallback_to_template": n - g,
           "median_secs": round(statistics.median(r["secs"] for r in rows), 2)}
print(json.dumps(summary))
json.dump({"summary": summary, "rows": rows}, open(os.path.join(os.path.dirname(__file__), f"results_{sys.argv[2]}.json"), "w"), indent=1)
