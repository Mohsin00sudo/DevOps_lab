import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app import app, FEATURES

PAYLOAD = json.loads((ROOT / "backend/test_payload.json").read_text(encoding="utf-8"))


def test_health():
    response = app.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json()["features"] == len(FEATURES)


def test_predict_valid():
    response = app.test_client().post("/predict", json=PAYLOAD)
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    assert body["prediction"] in ("attack", "normal")
    assert abs(sum(body["probabilities"]) - 1) < 1e-9
    assert len(body["classes"]) == len(body["probabilities"])


def test_predict_missing_feature():
    incomplete = dict(PAYLOAD)
    incomplete.pop(FEATURES[0])
    response = app.test_client().post("/predict", json=incomplete)
    assert response.status_code == 400


def test_predict_invalid_json():
    response = app.test_client().post("/predict", data="not-json",
                                      content_type="application/json")
    assert response.status_code == 400


def test_predict_extra_feature():
    response = app.test_client().post("/predict", json={**PAYLOAD, "attack_type": "smurf"})
    assert response.status_code == 400
    assert response.get_json()["extra"] == ["attack_type"]


def test_predict_unknown_category():
    response = app.test_client().post("/predict", json={**PAYLOAD, "protocol_type": "sctp"})
    assert response.status_code == 400


def test_predict_out_of_range_and_wrong_type():
    for bad in ({"serror_rate": 1.5}, {"src_bytes": -1}, {"duration": "ten"}):
        response = app.test_client().post("/predict", json={**PAYLOAD, **bad})
        assert response.status_code == 400, bad
