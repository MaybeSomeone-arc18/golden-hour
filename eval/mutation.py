"""Does the validator catch wrong sentences? Build correct sentences from random facts, corrupt each one
in a known way, and count how many corrupted sentences are rejected. Compares against the first, numbers-only check."""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from golden_hour.nudge import valid

def old_valid(text, f):  # first version: every number must be one of the facts, no units
    import re
    hh, mm = f["start"][11:16].split(":")
    ok = {str(f["temp"]), str(f["rain_prob"]), str(f["wind"]), f["start"][11:16], hh, str(int(hh)), mm, str(int(mm)), "0"}
    return bool(text.strip()) and set(re.findall(r"\d+(?:[.:]\d+)?", text)) <= ok

random.seed(7)
def facts():
    h = random.randint(5, 20)
    return {"start": f"2026-10-07T{h:02d}:00", "temp": random.randint(4, 36), "rain_prob": random.choice([0, 3, 9, 15, 30, 60, 85]),
            "wind": random.randint(2, 30), "day": random.choice(["today", "tomorrow"])}

def good(f, p="Pune"):
    return f"Go {f['day']} at {f['start'][11:16]} in {p}: {f['temp']}C, {f['rain_prob']}% rain chance, wind {f['wind']} km/h."

def swap_values(f):  # state the right numbers against the wrong labels
    return f"Go {f['day']} at {f['start'][11:16]}, it is {f['wind']}C with a {f['temp']}% rain chance."
def temp_is_hour(f):  # temperature equal to the start hour (the hole in the first check)
    h = int(f["start"][11:13]); return f"Go {f['day']} at {f['start'][11:16]}, it is {h}C with {f['rain_prob']}% rain chance."
def wrong_number(f):
    return good({**f, "temp": f["temp"] + random.choice([-5, -3, 4, 7])})
def wrong_day(f):
    return good({**f, "day": "tomorrow" if f["day"] == "today" else "today"}).replace(f"Go {f['day']}", "Go " + ("tomorrow" if f["day"] == "today" else "today"))
def sunny(f): return good(f).replace("Go", "Enjoy a sunny walk. Go", 1)
def wrong_weather(f):
    if f["rain_prob"] < 50: return good(f).replace("Go", "Take an umbrella, showers. Go", 1)
    return good(f).replace("Go", "It is dry out. Go", 1)

CASES = {"correct sentence (should be accepted)": good, "wrong number": wrong_number, "right numbers, wrong labels": swap_values,
         "temperature equals the start hour": temp_is_hour, "wrong day word": wrong_day, "invented 'sunny'": sunny,
         "weather word the facts contradict": wrong_weather}
N = 400
print(f"{'case':44s} {'first check':>12s} {'now':>8s}   (share of {N} flagged as bad; correct row = accepted)")
for name, fn in CASES.items():
    a = b = 0
    for _ in range(N):
        f = facts(); t = fn(f)
        a += old_valid(t, f); b += valid(t, f)
    if name.startswith("correct"):
        print(f"{name:44s} {a/N:12.0%} {b/N:8.0%}")
    else:
        print(f"{name:44s} {1-a/N:12.0%} {1-b/N:8.0%}")
