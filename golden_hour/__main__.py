import argparse, json, sys, time, urllib.request
from datetime import datetime, timezone, timedelta
from .scorer import parse, best_window
from .nudge import make

def fetch(lat, lon):
    u = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
         "&hourly=temperature_2m,precipitation_probability,wind_speed_10m,uv_index,is_day"
         "&forecast_days=2&timezone=auto")
    return json.load(urllib.request.urlopen(u, timeout=20))

def main():
    p = argparse.ArgumentParser(prog="golden-hour", description="Find the best hour to go outside.")
    p.add_argument("--lat", type=float, required=True); p.add_argument("--lon", type=float, required=True)
    p.add_argument("--place", default="your area"); p.add_argument("--minutes", type=int, default=60)
    p.add_argument("--model", help="path to a Gemma GGUF; without it a template sentence is used")
    a = p.parse_args()
    api = fetch(a.lat, a.lon)
    now = (datetime.now(timezone.utc) + timedelta(seconds=api.get("utc_offset_seconds", 0))).strftime("%Y-%m-%dT%H:%M")
    f = best_window(parse(api), now, a.minutes)
    if not f:
        sys.exit("no forecast window found")
    llm = None
    if a.model:
        from llama_cpp import Llama
        llm = Llama(model_path=a.model, n_ctx=1024, n_threads=2, verbose=False)
    f['day'] = 'today' if f['start'][:10] == now[:10] else 'tomorrow'
    text, src = make(f, a.place, llm)
    print(text); print(f"[{src}] score {f['score']}/100, UV {f['uv']}, daylight {f['daylight']}")

if __name__ == "__main__":
    main()
