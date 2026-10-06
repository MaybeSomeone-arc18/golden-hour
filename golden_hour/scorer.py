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

# points per unit, see docs/scoring.md. Judgment, not fitted. eval/sensitivity.py perturbs them.
WEIGHTS = {"cold": 3.0, "heat": 5.0, "rain": 0.6, "wind": 1.5, "uv": 6.0, "night": 25.0}

def penalties(h: Hour, w: dict = None) -> dict:
    """Points lost per factor. comfort() is 100 minus the sum, clamped."""
    w = w or WEIGHTS
    return {
        "temp": (18 - h.temp) * w["cold"] if h.temp < 18 else max(0, h.temp - 24) * w["heat"],
        "rain": h.rain_prob * w["rain"],
        "wind": max(0, h.wind - 15) * w["wind"],
        "uv": max(0, h.uv - 5) * w["uv"],
        "night": 0.0 if h.is_day else w["night"],
    }

def comfort(h: Hour, w: dict = None) -> float:
    """0..100. Penalties are simple and listed in docs/scoring.md."""
    return max(0.0, min(100.0, 100.0 - sum(penalties(h, w).values())))

def why(w: list) -> str:
    """One plain line on what cost points (or that nothing did), averaged over the walk's hours."""
    tot = {k: sum(penalties(x)[k] for x in w) / len(w) for k in ("temp", "rain", "wind", "uv", "night")}
    names = {"temp": "temperature outside 18-24C", "rain": "rain chance", "wind": "wind", "uv": "UV", "night": "darkness"}
    lost = sorted(((v, k) for k, v in tot.items() if v >= 3), reverse=True)
    if not lost:
        return "nothing cost more than 3 points: mild, dry, calm, daylight"
    return "lost points to " + ", ".join(f"{names[k]} (-{round(v)})" for v, k in lost[:2])

def parse(api: dict) -> list:
    h = api["hourly"]
    return [Hour(h["time"][i], h["temperature_2m"][i], h["precipitation_probability"][i] or 0,
                 h["wind_speed_10m"][i], h["uv_index"][i] or 0, bool(h["is_day"][i]))
            for i in range(len(h["time"]))]

def best_window(hours, now: str, minutes: int = 60, horizon: int = 24, weights: dict = None):
    """Best start hour in the next `horizon` hours; the walk spans ceil(minutes/60) hours."""
    span = max(1, -(-minutes // 60))
    cand = [i for i, h in enumerate(hours) if h.time >= now[:13] + ":00"][:horizon]
    best = None
    for i in cand:
        win = hours[i:i + span]
        if len(win) < span:
            continue
        sc = sum(comfort(x, weights) for x in win) / span
        if best is None or sc > best[0]:
            best = (sc, win)
    if best is None:
        return None
    sc, w = best
    return {"start": w[0].time, "score": round(sc), "temp": round(sum(x.temp for x in w) / span),
            "rain_prob": round(max(x.rain_prob for x in w)), "wind": round(max(x.wind for x in w)),
            "uv": round(max(x.uv for x in w), 1), "daylight": all(x.is_day for x in w), "why": why(w)}
