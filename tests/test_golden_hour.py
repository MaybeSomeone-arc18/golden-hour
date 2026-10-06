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

from golden_hour.scorer import penalties, why
def test_penalties_sum_matches_comfort():
    x = h("x", temp=30, rain=40, wind=25)
    assert comfort(x) == 100 - sum(penalties(x).values())
def test_why_names_biggest_loss():
    assert "rain" in why([h("x", rain=90)]) and "temperature" not in why([h("x", rain=90)])
def test_why_says_nothing_lost_for_perfect_hour(): assert why([h("x")]).startswith("nothing cost")
def test_validator_rejects_temp_equal_to_start_hour():
    f = {"start": "2026-10-07T06:00", "temp": 21, "rain_prob": 9, "wind": 6, "day": "tomorrow"}
    assert not valid("Go tomorrow at 06:00, it is 6C.", f)
def test_validator_rejects_wrong_day_and_invented_sun():
    f = {"start": "2026-10-07T06:00", "temp": 21, "rain_prob": 9, "wind": 6, "day": "tomorrow"}
    assert not valid("Go today at 06:00, 21C.", f) and not valid("A sunny walk at 06:00, 21C.", f)
def test_validator_accepts_bare_hour_after_at():
    f = {"start": "2026-10-07T06:00", "temp": 21, "rain_prob": 9, "wind": 6, "day": "tomorrow"}
    assert valid("Go tomorrow at 6, about 21C.", f)

def test_poor_day_says_so_and_skips_model():
    f = {"start": "2026-10-07T18:00", "temp": 22, "rain_prob": 92, "wind": 14, "day": "today", "score": 41}
    text, src = make(f, "Nairobi", Fake("Enjoy a lovely walk at 18:00, 22C!"))
    assert src == "template" and text.startswith("No good window")

def test_validator_accepts_12_hour_time_for_same_moment():
    f = {"start": "2026-10-07T18:00", "temp": 16, "rain_prob": 2, "wind": 23, "day": "tomorrow"}
    assert valid("Go tomorrow at 6:00 PM, 16C.", f) and not valid("Go tomorrow at 6:00 AM, 16C.", f)
def test_validator_rejects_light_rain_when_rain_chance_is_2():
    f = {"start": "2026-10-07T18:00", "temp": 16, "rain_prob": 2, "wind": 23, "day": "tomorrow"}
    assert not valid("Go tomorrow at 18:00, 16C and light rain.", f)

def test_light_rain_chance_is_a_description_not_a_claim_of_rain():
    f = {"start": "2026-10-07T18:00", "temp": 16, "rain_prob": 12, "wind": 5, "day": "tomorrow"}
    assert valid("Go tomorrow at 18:00, 16C with a light rain chance.", f)
