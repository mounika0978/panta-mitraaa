"""Rules engine tests, including exact-threshold boundaries and 'highest risk wins'."""
import pytest

from app.rules.advice import get_advice, growth_stage
from app.rules.dry_spell import evaluate


def facts(rain=20.0, dry=0, forecast=20.0):
    return {"rain_7d_mm": rain, "consecutive_dry_days": dry, "forecast_5d_mm": forecast}


@pytest.mark.parametrize("f, expected", [
    (facts(38, 1, 22), "low"),            # normal season
    (facts(20, 6, 20), "low"),            # one day below the 7-day threshold
    (facts(20, 7, 20), "medium"),         # exactly at the threshold (>=)
    (facts(20, 14, 20), "medium"),        # one day below the high threshold
    (facts(20, 15, 20), "high"),          # exactly at the high threshold
    (facts(20, 10, 4.9), "high"),         # long dry + very low forecast
    (facts(20, 10, 5.0), "medium"),       # forecast exactly 5 is NOT below 5
    (facts(9.9, 0, 9.9), "medium"),       # low rain now and low forecast
    (facts(10.0, 0, 9.9), "low"),         # rain exactly 10 is not below 10
])
def test_risk_levels(f, expected):
    assert evaluate(f)["risk"] == expected


def test_highest_risk_wins_and_all_fired_ids_returned():
    out = evaluate(facts(0, 16, 2))
    assert out["risk"] == "high"
    assert {"DS-L0", "DS-M1", "DS-M2", "DS-H1", "DS-H2"} <= set(out["fired_ids"])
    assert all(r["id"].startswith("DS-H") for r in out["reasons"])


@pytest.mark.parametrize("das, expected", [(-1, "pre_sowing"), (0, "establishment"), (20, "establishment"),
                                           (21, "flowering_pegging"), (130, "maturity"), (131, "post_maturity")])
def test_growth_stage_boundaries(das, expected):
    assert growth_stage("groundnut", das)["id"] == expected


def test_specific_advice_comes_before_generic():
    ids = get_advice("groundnut", "flowering_pegging", "high")["rule_ids"]
    assert ids[0] == "ADV-GN-FLW-HIGH" and "ADV-ANY-HIGH" in ids


def test_wildcard_advice_when_no_specific_rule():
    assert get_advice("millet", "establishment", "low")["rule_ids"] == ["ADV-ANY-LOW"]
