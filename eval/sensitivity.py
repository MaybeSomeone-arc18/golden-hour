"""How much do my judgment weights matter? Re-pick the best hour with every weight randomly scaled by 0.7x to 1.3x
and count how often the pick moves. Uses live forecasts for the cities in cities.json."""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from datetime import datetime, timezone, timedelta
from golden_hour.__main__ import fetch
from golden_hour.scorer import parse, best_window, WEIGHTS
random.seed(11)
cities = json.load(open(os.path.join(os.path.dirname(__file__), "cities.json")))
same = within1 = total = 0
moved = []
for name, lat, lon in cities:
    api = fetch(lat, lon); H = parse(api)
    now = (datetime.now(timezone.utc) + timedelta(seconds=api["utc_offset_seconds"])).strftime("%Y-%m-%dT%H:%M")
    for minutes in (30, 60, 120):
        base = best_window(H, now, minutes)["start"]
        for _ in range(50):
            w = {k: v * random.uniform(0.7, 1.3) for k, v in WEIGHTS.items()}
            alt = best_window(H, now, minutes, weights=w)["start"]
            d = abs((datetime.fromisoformat(alt) - datetime.fromisoformat(base)).total_seconds()) / 3600
            total += 1; same += d == 0; within1 += d <= 1
            if d > 2: moved.append(name)
print(f"{total} re-picks (20 cities x 3 walk lengths x 50 random weight sets, each weight scaled 0.7x-1.3x)")
print(f"same hour: {same/total:.0%}   within 1 hour: {within1/total:.0%}   moved more than 2 hours: {len(moved)/total:.0%}")
if moved:
    import collections
    print("cities where it moved more than 2 hours:", dict(collections.Counter(moved)))
