"""Turn the scorer's facts into one friendly sentence with a local open-weight model (Gemma 3 1B).
The model never decides anything. Every number it writes is checked against the facts,
and a plain template is used if the check fails."""
import re

POOR = 60  # below this score there is no good window, and the app says so instead of cheering

def template(f: dict, place: str) -> str:
    rain = "dry" if f["rain_prob"] < 20 else f"{f['rain_prob']}% chance of rain"
    d = f.get("day", "")
    if f.get("score", 100) < POOR:
        return (f"No good window in the next 24 hours in {place}. Least bad: {d + ' ' if d else ''}at {f['start'][11:16]}, "
                f"{f['temp']}C, {rain}, wind {f['wind']} km/h.")
    return (f"Go {d + ' ' if d else ''}at {f['start'][11:16]} in {place}: {f['temp']}C, {rain}, wind {f['wind']} km/h.")

def prompt(f: dict, place: str) -> str:
    return ("Write ONE short, warm sentence (max 28 words) telling someone to go for a walk. "
            "Use only these facts and copy numbers exactly. Do not add other numbers, places or activities.\n"
            f"Place: {place}. Start: {f.get('day','')} {f['start'][11:16]}. Temperature: {f['temp']}C. "
            f"Rain chance: {f['rain_prob']}%. Wind: {f['wind']} km/h.")

NUM = re.compile(r"(\d+(?:[.:]\d+)?)(\s*(?:°\s*C|°|C\b|degrees?|%|km/h|kph))?", re.I)

def _unit(u: str) -> str:
    u = (u or "").strip().lower().replace(" ", "")
    if u in ("%",): return "pct"
    if u in ("km/h", "kph"): return "wind"
    if u: return "temp"
    return ""

def numbers(text: str) -> set:
    return set(m.group(1) for m in NUM.finditer(text))

# word claims the forecast facts cannot support unless the fact says so
CLAIMS = {
    "rain":  (("drizzle", "shower", "showers", "storm", "umbrella", "snow", "thunder", "downpour", "wet", "rainy"),
              lambda f: f["rain_prob"] >= 50),
    "lightrain": (("light rain", "rainfall"), lambda f: f["rain_prob"] >= 30),
    "sun":   (("sunny", "sunshine", "cloudless", "clear sky", "clear skies"), lambda f: False),
    "wind":  (("windy", "gusty", "breezy"), lambda f: f["wind"] >= 15),
    "hot":   (("hot", "scorching", "sweltering"), lambda f: f["temp"] >= 30),
    "cold":  (("cold", "chilly", "freezing", "frosty"), lambda f: f["temp"] <= 12),
    "dry":   (("dry",), lambda f: f["rain_prob"] < 20),
}

def valid(text: str, f: dict) -> bool:
    """Numbers must carry the right unit and value, the day word must match, and weather words
    the facts do not support are rejected. Checks facts, not tone."""
    t = text.strip()
    if not t or len(t.split()) > 40:
        return False
    hh, mm = f["start"][11:16].split(":")
    low = t.lower().replace("light rain chance", "rain chance").replace("slight rain chance", "rain chance")
    for m in NUM.finditer(t):
        n, u = m.group(1), _unit(m.group(2))
        if ":" in n:
            ok_times = {f["start"][11:16], f"{int(hh)}:{mm}"}
            ap = re.match(r"\s*([ap])\.?m", low[m.end():])
            if ap:  # a 12-hour clock time is fine if it names the same moment
                h12 = int(n.split(":")[0]) % 12 + (12 if ap.group(1) == "p" else 0)
                ok_times = {f"{h12:02d}:{n.split(':')[1]}"}
            if n not in ok_times and not (ap and f"{h12:02d}:{n.split(':')[1]}" == f["start"][11:16]):
                return False
        elif u == "temp":
            if n != str(f["temp"]): return False
        elif u == "pct":
            if n != str(f["rain_prob"]): return False
        elif u == "wind":
            if n != str(f["wind"]): return False
        else:
            # a bare number is only allowed as the hour right after "at"
            before = low[:m.start()].rstrip()
            if not (before.endswith("at") and n in (str(int(hh)), hh)):
                return False
    day = f.get("day", "")
    if day == "today" and re.search(r"\b(tomorrow|tonight)\b", low): return False
    if day == "tomorrow" and re.search(r"\b(today|tonight)\b", low): return False
    for words, supported in CLAIMS.values():
        if any(re.search(r"\b" + re.escape(w) + r"\b", low) for w in words) and not supported(f):
            return False
    return True

def make(f: dict, place: str, llm=None):
    """Returns (sentence, source) where source is 'gemma' or 'template'."""
    if llm is not None and f.get("score", 100) >= POOR:
        r = llm.create_chat_completion(messages=[{"role": "user", "content": prompt(f, place)}],
                                       max_tokens=70, temperature=0.2)
        t = r["choices"][0]["message"]["content"].strip().replace("\n", " ").strip('"*')
        make.last_raw = t
        if valid(t, f):
            return t, "gemma"
    return template(f, place), "template"
