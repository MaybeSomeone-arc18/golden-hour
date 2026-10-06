from golden_hour.scorer import Hour, comfort, best_window
from golden_hour.nudge import valid, template, make, numbers

def h(t, temp=18, rain=0, wind=5, uv=2, day=True): return Hour(t, temp, rain, wind, uv, day)

def test_perfect_hour_scores_100(): assert comfort(h("2026-10-06T17:00")) == 100
def test_rain_hurts(): assert comfort(h("x", rain=100)) <= 40
def test_heat_hurts_more_than_cool(): assert comfort(h("x", temp=34)) < comfort(h("x", temp=8))
def test_night_penalty(): assert comfort(h("x", day=False)) == 75
def test_best_window_picks_dry_hour():
    hrs = [h("2026-10-06T10:00", rain=90), h("2026-10-06T11:00"), h("2026-10-06T12:00", rain=80)]
    assert best_window(hrs, "2026-10-06T09:30")["start"] == "2026-10-06T11:00"
def test_window_skips_past_hours():
    hrs = [h("2026-10-06T08:00"), h("2026-10-06T09:00", rain=50)]
    assert best_window(hrs, "2026-10-06T09:10", 60)["start"] == "2026-10-06T09:00"
def test_multi_hour_walk_needs_full_span():
    hrs = [h("2026-10-06T10:00"), h("2026-10-06T11:00", rain=100)]
    assert best_window(hrs, "2026-10-06T10:00", 120)["score"] < 100
F = {"start": "2026-10-06T17:00", "temp": 14, "rain_prob": 9, "wind": 11, "uv": 1, "daylight": True}
def test_validator_accepts_matching_numbers(): assert valid("Go at 17:00, it is 14C with a 9% rain chance and 11 km/h wind.", F)
def test_validator_rejects_invented_number(): assert not valid("Go at 17:00, it is 21C.", F)
def test_validator_rejects_empty(): assert not valid("  ", F)
def test_template_has_facts(): assert "17:00" in template(F, "Pune") and "14C" in template(F, "Pune")
class Fake:
    def __init__(s, t): s.t = t
    def create_chat_completion(s, **k): return {"choices": [{"message": {"content": s.t}}]}
def test_make_falls_back_on_bad_number(): assert make(F, "Pune", Fake("It is 30C, go!"))[1] == "template"
def test_make_uses_model_when_valid(): assert make(F, "Pune", Fake("Go at 17:00, 14C and calm."))[1] == "gemma"
