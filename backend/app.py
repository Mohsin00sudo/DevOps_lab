from pathlib import Path
import math
import joblib
import pandas as pd
from flask import Flask, jsonify, request

BASE = Path(__file__).resolve().parent
BUNDLE = joblib.load(BASE / "models/model_bundle.joblib")
MODEL = BUNDLE["pipeline"]
FEATURES = BUNDLE["features"]
TASK = BUNDLE.get("task", "classification")
CLASSES = BUNDLE.get("classes", [])
SCHEMA = {f["name"]: f for f in BUNDLE.get("schema", [])}
app = Flask(__name__)


def validate_values(data):
    """Type, range and allowed-category checks driven by the saved schema."""
    errors = []
    for name in FEATURES:
        spec, value = SCHEMA.get(name), data[name]
        if spec is None:
            continue
        if spec["kind"] == "category":
            if value not in spec["options"]:
                errors.append(f"{name}: '{value}' is not an allowed category")
        elif (isinstance(value, bool) or not isinstance(value, (int, float))
              or not math.isfinite(value)):
            errors.append(f"{name}: expected a number")
        elif value < spec.get("min", -math.inf) or value > spec.get("max", math.inf):
            errors.append(f"{name}: {value} outside "
                          f"[{spec.get('min')}, {spec.get('max', 'inf')}]")
    return errors


@app.get("/health")
def health():
    return jsonify(status="ok", features=len(FEATURES), task=TASK,
                   model_version=BUNDLE.get("model_version"))


@app.post("/predict")
def predict():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Expected a JSON object"), 400
    missing = [f for f in FEATURES if f not in data]
    extra = [f for f in data if f not in FEATURES]
    if missing or extra:
        return jsonify(error="Input schema mismatch",
                       missing=missing, extra=extra), 400
    invalid = validate_values(data)
    if invalid:
        return jsonify(error="Invalid input values", detail=invalid), 400
    frame = pd.DataFrame([[data[f] for f in FEATURES]], columns=FEATURES)
    try:
        prediction = MODEL.predict(frame)[0]
        prediction = (prediction.item() if hasattr(prediction, "item")
                      else prediction)
        result = {"prediction": prediction, "task": TASK,
                  "model_version": BUNDLE.get("model_version"),
                  "disclaimer": "Research/teaching prototype only. "
                                "Not a production intrusion detection system."}
        if TASK == "classification" and hasattr(MODEL, "predict_proba"):
            result["probabilities"] = MODEL.predict_proba(frame)[0].tolist()
            result["classes"] = CLASSES
        return jsonify(result)
    except (ValueError, TypeError) as exc:
        return jsonify(error="Invalid input", detail=str(exc)), 400
    except Exception:
        app.logger.exception("Prediction failed")
        return jsonify(error="Prediction processing failed"), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
