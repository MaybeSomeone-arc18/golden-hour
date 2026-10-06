"""Turn the scorer's facts into one friendly sentence with a local open-weight model (Gemma 3 1B).
The model never decides anything. Every number it writes is checked against the facts,
and a plain template is used if the check fails."""
import re

def template(f: dict, place: str) -> str:
    rain = "dry" if f["rain_prob"] < 20 else f"{f['rain_prob']}% chance of rain"
    d = f.get("day", "")
    return (f"Go {d + ' ' if d else ''}at {f['start'][11:16]} in {place}: {f['temp']}C, {rain}, wind {f['wind']} km/h.")

def prompt(f: dict, place: str) -> str:
    return ("Write ONE short, warm sentence (max 28 words) telling someone to go for a walk. "
            "Use only these facts and copy numbers exactly. Do not add other numbers, places or activities.\n"
            f"Place: {place}. Start: {f.get('day','')} {f['start'][11:16]}. Temperature: {f['temp']}C. "
            f"Rain chance: {f['rain_prob']}%. Wind: {f['wind']} km/h.")

def numbers(text: str) -> set:
    return set(re.findall(r"\d+(?:[.:]\d+)?", text))

def allowed(f: dict) -> set:
    hh, mm = f["start"][11:16].split(":")
    return {str(f["temp"]), str(f["rain_prob"]), str(f["wind"]), f["start"][11:16], hh, str(int(hh)), mm, str(int(mm)), "0"}

def valid(text: str, f: dict) -> bool:
    ok = allowed(f)
    return bool(text.strip()) and numbers(text) <= ok and len(text.split()) <= 40

def make(f: dict, place: str, llm=None):
    """Returns (sentence, source) where source is 'gemma' or 'template'."""
    if llm is not None:
        r = llm.create_chat_completion(messages=[{"role": "user", "content": prompt(f, place)}],
                                       max_tokens=70, temperature=0.2)
        t = r["choices"][0]["message"]["content"].strip().replace("\n", " ").strip('"*')
        if valid(t, f):
            return t, "gemma"
    return template(f, place), "template"
