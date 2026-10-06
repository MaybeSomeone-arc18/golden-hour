"""Rank the next hours for a walk. Pure rules, no model. Inputs come from Open-Meteo."""
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Hour:
    time: str          # "2026-10-06T17:00" local
    temp: float        # C
    rain_prob: float   # %
    wind: float        # km/h
    uv: float
    is_day: bool

def comfort(h: Hour) -> float:
    """0..100. Penalties are simple and listed in docs/scoring.md."""
    s = 100.0
    s -= abs(h.temp - 18) * 3.0 if h.temp < 18 else max(0, h.temp - 24) * 5.0
    s -= h.rain_prob * 0.6
    s -= max(0, h.wind - 15) * 1.5
    s -= max(0, h.uv - 5) * 6.0
    if not h.is_day:
        s -= 25
    return max(0.0, min(100.0, s))

def parse(api: dict) -> list:
    h = api["hourly"]
    return [Hour(h["time"][i], h["temperature_2m"][i], h["precipitation_probability"][i] or 0,
                 h["wind_speed_10m"][i], h["uv_index"][i] or 0, bool(h["is_day"][i]))
            for i in range(len(h["time"]))]

def best_window(hours, now: str, minutes: int = 60, horizon: int = 24):
    """Best start hour in the next `horizon` hours; the walk spans ceil(minutes/60) hours."""
    span = max(1, -(-minutes // 60))
    cand = [i for i, h in enumerate(hours) if h.time >= now[:13] + ":00"][:horizon]
    best = None
    for i in cand:
        w = hours[i:i + span]
        if len(w) < span:
            continue
        sc = sum(comfort(x) for x in w) / span
        if best is None or sc > best[0]:
            best = (sc, i, w)
    if best is None:
        return None
    sc, i, w = best
    return {"start": w[0].time, "score": round(sc), "temp": round(sum(x.temp for x in w) / span),
            "rain_prob": round(max(x.rain_prob for x in w)), "wind": round(max(x.wind for x in w)),
            "uv": round(max(x.uv for x in w), 1), "daylight": all(x.is_day for x in w)}
