"""Safety tests: no doses in any advice text, public pages mask mobile numbers, chat refuses dose questions."""
import re

from app import config

DOSE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:kg|g|gm|gms|gram|grams|ml|l|litre|litres|liter|liters)\b|per\s+acre|ఎకరాకు", re.I)
MOBILE = "9876543210"


def _texts(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if not k.startswith("_") and k not in ("keywords", "dose_terms_ascii", "dose_terms_te", "advisory_terms"):
                yield from _texts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _texts(v)


def test_dose_pattern_detects_examples():
    for bad in ("apply 5 kg now", "use 200 ml", "2 litre mix", "30 g seed", "one bag per acre"):
        assert DOSE.search(bad), bad


def test_advice_rules_have_no_doses():
    for t in _texts(config.load_json("data/rules/advice_rules.json")):
        assert not DOSE.search(t), t


def test_chat_answers_have_no_doses():
    for t in _texts(config.load_json("data/rules/chat_faq.json")):
        assert not DOSE.search(t), t


def test_public_pages_mask_mobile(client, farmer_id):
    pages = [client.get("/").text, client.get(f"/farmers/{farmer_id}").text,
             client.get(f"/farmers/lookup?mobile={MOBILE}").text, client.get("/callback").text, client.get("/upload").text]
    done = client.post("/callback", data={"name": "A", "mobile": MOBILE, "village": "V", "concern": "help", "consent": "on"})
    pages.append(done.text)
    for html in pages:
        assert MOBILE not in html
    assert "****3210" in done.text


def test_consent_is_required(client):
    r = client.post("/callback", data={"name": "A", "mobile": MOBILE, "village": "V", "concern": "help"})
    assert r.status_code == 422


def test_advisory_page_has_disclaimer_and_rule_ids(client, farmer_id):
    html = client.get(f"/farmers/{farmer_id}?scenario=severe_dry_spell").text
    assert "does not guarantee rain, yield, or income" in html
    assert "DS-H1" in html and "ADV-ANY-HIGH" in html


def test_chat_refuses_dose_questions(client):
    out = client.post("/api/chat", json={"message": "how much urea per acre?"}).json()
    assert out["rule_ids"] == ["SAFETY-NO-DOSE"]


def test_chat_advisory_cites_rule_ids(client, farmer_id):
    out = client.post("/api/chat", json={"message": "what is my risk", "farmer_id": farmer_id, "scenario": "severe_dry_spell"}).json()
    assert "DS-H1" in out["rule_ids"]


def test_admin_requires_password(client):
    assert client.get("/admin/callbacks").status_code == 401
    assert client.get("/admin/callbacks", auth=("admin", "wrong")).status_code == 401
    assert client.get("/admin/callbacks", auth=("admin", "testpw")).status_code == 200


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"
