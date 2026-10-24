from pathlib import Path
import json
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
bundle = joblib.load(ROOT / "backend/models/model_bundle.joblib")
with (ROOT / "backend/test_payload.json").open(encoding="utf-8") as f:
    payload = json.load(f)
features = bundle["features"]
assert set(features) == set(payload), "Payload keys must match features"
frame = pd.DataFrame([[payload[f] for f in features]], columns=features)
model = bundle["pipeline"]
prediction = model.predict(frame).tolist()
print("Prediction:", prediction)
if hasattr(model, "predict_proba"):
    probabilities = model.predict_proba(frame)[0].round(6).tolist()
    print("Classes:", bundle["classes"])
    print("Probabilities:", probabilities)

# Compare with the output recorded by the training notebook for the SAME sample
expected = json.loads((ROOT / "docs/expected_sample_output.json").read_text())
assert prediction[0] == expected["prediction"], (prediction, expected)
assert max(abs(a - b) for a, b in zip(probabilities, expected["probabilities"])) < 1e-6
print("Matches training notebook:", expected)
print("PASS: local inference")
