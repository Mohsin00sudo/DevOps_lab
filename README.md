# Network Intrusion Detection: Full-Stack ML Application

A trained scikit-learn model that classifies a network connection record as **`attack`** or **`normal`**. It is served by a **Flask REST API**, has an **Angular 22** input form, and is checked and deployed by **GitHub Actions** and **GitHub Pages**.

> Research and teaching prototype only. This is not a production intrusion detection system.

| | |
|---|---|
| Problem type | Binary classification (`attack` / `normal`) |
| Dataset | NSL-KDD `KDDTrain+` (125,973 rows × 43 columns) plus the official `KDDTest+` (22,544 rows) |
| Model | sklearn `Pipeline`: `log1p` + `StandardScaler` (37 numeric), `OneHotEncoder` (3 categorical), `LogisticRegression` |
| Model artifact | `backend/models/model_bundle.joblib`, with keys `pipeline`, `features`, `task`, `model_version` (+ `classes`, `schema`, `metrics`) |
| Training notebook | `notebooks/train_model.ipynb` |
| Versions | Python 3.12, scikit-learn 1.9.1, Node.js 24 LTS (CI), Angular CLI 22.2 |
| GitHub repo | https://github.com/Mohsin00sudo/DevOps_lab |
| GitHub Pages | https://mohsin00sudo.github.io/DevOps_lab/ *(static UI only)* |

## Architecture

```
Browser / Angular form (http://localhost:4200)
      |   POST /api/predict (JSON)
      v
Angular dev proxy  ->  Flask API (http://127.0.0.1:5000)
      | schema + range/category validation -> fitted preprocessing -> LogisticRegression
      v
JSON prediction + class probabilities -> Angular result panel

Git repository -> GitHub Actions (pytest + Angular build/test)
               -> GitHub Pages (STATIC ANGULAR ONLY, prediction disabled)
```

## Model provenance

* **Data:** NSL-KDD by Tavallaee, Bagheri, Lu and Ghorbani (2009), Canadian Institute for Cybersecurity, University of New Brunswick. It is a refined version of KDD Cup 1999 with duplicate records removed. The records are **simulated military-network traffic and contain no personal data**. The training notebook downloads the raw files into `data/`. They are not committed; only the one-row `data/sample_inputs.csv` is.
* **Target:** `attack_type == "normal"` becomes `normal`, and every other attack type becomes `attack`.
* **Excluded:** `attack_type` (the target), `difficulty_level` (dataset metadata that would leak information), and `num_outbound_cmds` (always 0).
* **Split:** stratified 80/20 train/validation split of `KDDTrain+`, plus the official `KDDTest+`. The preprocessing is fitted on the training rows only and saved inside the pipeline.

| Split | Accuracy | Precision (attack) | Recall (attack) | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Validation (20% of KDDTrain+) | 0.986 | 0.986 | 0.984 | 0.985 | 0.998 |
| Official KDDTest+ | 0.745 | 0.913 | 0.610 | 0.731 | 0.801 |

`KDDTest+` contains **17 attack types that never appear in training** (for example `mailbomb`, `apache2` and `processtable`). The drop in recall there is the well-known NSL-KDD generalisation gap, not a bug.

## Input schema (40 features, in this exact order)

| Group | Features | Type / range |
|---|---|---|
| Basic connection | `duration`, `protocol_type`, `service`, `flag`, `src_bytes`, `dst_bytes`, `land`, `wrong_fragment`, `urgent` | `protocol_type` has 3 options, `service` has 70, `flag` has 11; numbers ≥ 0; `land` is 0/1 |
| Content | `hot`, `num_failed_logins`, `logged_in`, `num_compromised`, `root_shell`, `su_attempted`, `num_root`, `num_file_creations`, `num_shells`, `num_access_files`, `is_host_login`, `is_guest_login` | counts ≥ 0; the 0/1 flags are capped at 1 |
| Time-based (2 s window) | `count`, `srv_count`, `serror_rate`, `srv_serror_rate`, `rerror_rate`, `srv_rerror_rate`, `same_srv_rate`, `diff_srv_rate`, `srv_diff_host_rate` | counts 0–511; rates 0–1 |
| Host-based (100 connections) | `dst_host_count`, `dst_host_srv_count`, `dst_host_same_srv_rate`, `dst_host_diff_srv_rate`, `dst_host_same_src_port_rate`, `dst_host_srv_diff_host_rate`, `dst_host_serror_rate`, `dst_host_srv_serror_rate`, `dst_host_rerror_rate`, `dst_host_srv_rerror_rate` | counts 0–255; rates 0–1 |

The schema (options and ranges) is stored inside the model bundle. `backend/export_schema.py` generates `frontend/src/app/feature-schema.ts` from it, so the form and the model cannot drift apart. The API rejects missing or extra fields, unknown categories, non-numeric values and out-of-range values with HTTP 400.

## Project structure

```
.
├── backend/
│   ├── app.py                 Flask API: GET /health, POST /predict
│   ├── make_payload.py        data/sample_inputs.csv -> test_payload.json
│   ├── test_pipeline.py       direct inference, compared with the notebook output
│   ├── test_api.py            live HTTP test (requests, trust_env=False)
│   ├── export_schema.py       bundle -> frontend/src/app/feature-schema.ts
│   ├── requirements.txt
│   ├── test_payload.json
│   ├── models/model_bundle.joblib
│   └── tests/ (test_api.py, test_structure.py)
├── data/sample_inputs.csv     one non-sensitive record (no target)
├── notebooks/train_model.ipynb
├── docs/                      environment.txt, expected_sample_output.json, evidence
├── frontend/                  Angular 22 standalone app (+ proxy.conf.json)
└── .github/workflows/         ci.yml, pages.yml
```

## Prerequisites

Git, Python 3.12 (`py -3.12`) and **Node.js 24 LTS** with npm. Angular 22 supports Node `^22.22.3 || ^24.15.0 || >=26`. Odd-numbered versions such as 25 only produce a warning.

## Installation (Windows PowerShell, from the project root)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope Process RemoteSigned
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
cd frontend; npm ci; cd ..
```

Optional, to retrain the model: `python -m pip install matplotlib nbclient ipykernel`. Then run `notebooks/train_model.ipynb` with the `.venv` kernel, followed by `python backend\make_payload.py` and `python backend\export_schema.py`.

## Running locally (three terminals)

| Terminal | Folder | Command | Keep open? |
|---|---|---|---|
| 1 — Flask | project root | `.\.venv\Scripts\Activate.ps1` then `python backend\app.py` | Yes |
| 2 — Angular | `frontend` | `npx ng serve --open --proxy-config proxy.conf.json` | Yes |
| 3 — Commands | project root | tests, curl, git | — |

Open http://localhost:4200, click **Load sample record** (or fill in all 40 fields), then click **Run local prediction**. The sample should return `attack` with about 98.7% probability.

Quick checks from Terminal 3:

```powershell
curl.exe --noproxy "*" -i http://127.0.0.1:5000/health
curl.exe --noproxy "*" -i -X POST "http://127.0.0.1:5000/predict" -H "Content-Type: application/json" --data-binary "@backend/test_payload.json"
curl.exe --noproxy "*" -i http://localhost:4200/api/health     # through the Angular proxy
```

## Tests

```powershell
python backend\test_pipeline.py          # direct inference = notebook output
python -m pytest -q backend\tests        # 8 tests: health, valid, missing, bad JSON, extra field, bad category, range/type, structure
python backend\test_api.py               # needs Flask running (Terminal 1)
cd frontend; npm run build; npx ng test --watch=false
```

## CI/CD and deployment boundary

* **`.github/workflows/ci.yml`** runs on every push or PR to `main`.
  * `backend` job: Python 3.12, `pip install -r backend/requirements.txt`, then the structure test, the model-dependent API tests and `test_pipeline.py`. The 6 KB model bundle is committed because it was trained on public, non-personal data, so these tests can run on the Linux runner.
  * `frontend` job: Node 24, `npm ci`, `npm run build`, the Angular unit tests, then uploads the `angular-build` artifact.
* **`.github/workflows/pages.yml`** builds a production bundle with `--base-href /<repo-name>/` (filled in automatically from the repository name) and deploys `frontend/dist/frontend/browser` to GitHub Pages. First set **Settings → Pages → Source → GitHub Actions**.
* **GitHub Pages hosts only static files.** It does not run Python, Flask or the model. On Pages the form renders, but **Run local prediction** is disabled and a notice is shown. Live public predictions would need a separately hosted, secured HTTPS backend.

## Ethics and limitations

NSL-KDD reflects 1998-era simulated traffic. It is a benchmark, not a representative sample of modern networks. The model must not be used to block or flag real traffic. Its probabilities are not calibrated security risk scores, and the recall of 0.61 on unseen attack types shows that it misses novel attacks.
