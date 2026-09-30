# Student-Complainify

AI-powered Student Complaint Classification and Management System. A Flask web app that automatically categorizes complaints into 10 categories using a from-scratch Multinomial Naive Bayes classifier, detects emotional tone using a lexicon-based sentiment analyzer, and provides role-based dashboards for both students and admins.

---

## How It Works

```
Student submits complaint
        |
        v
[Flask app.py] --> [Classifier]  --> category + confidence + tier
                --> [Sentiment]  --> trained NB (env.py) | rule fallback
                --> [Priority]   --> trained NB (env.py) | keyword fallback
        |
        v
Priority + sentiment stored alongside the complaint
        |
        v
Admin dashboard: complaint lists, sentiment badges, /admin/analysis heatmaps
```

### Core Components

#### 1. Naive Bayes Classifier (`ml/classifier.py`)
- Multinomial Naive Bayes written from scratch (no sklearn)
- Custom stemmer with 25 rules (no nltk)
- Bigram features (e.g. "wifi_router", "exam_schedule")
- Laplace smoothing (alpha=1.0), min_df=3
- Trained on 7204 samples, tested on 1806 (80/20 stratified split)
- Three-tier confidence:
  - **Auto** (>=90%): confident classification
  - **Suggest** (60-89%): probable but uncertain
  - **Unknown** (<60%): too ambiguous
- Rule-based override: complaints mentioning hackathon/event keywords auto-classify to Hackathon/Event

#### 2. Sentiment & Priority (ML-first, `ml/sentiment.py` + `ml/priority.py`)
- **12,000-row dataset** (`data/sentiment_dataset.csv`): hand-written curation + template-driven synthesis where sentiment and priority ground truth are decided at generation time (not by any classifier). Labeling convention: `negative` = strong complaint language (stale/rotten/broken/stolen/...); mild problem-reports ("water not getting on time, Wi-Fi issue") are `neutral` — urgency is handled by the priority column, not sentiment
- Two from-scratch Multinomial Naive Bayes models (`data/sentiment_model.json`, `data/priority_model.json`) trained with the same machinery as the category classifier — train with `python ml/train_sentiment_priority.py`
- `ml/env.py` lazy-loads both models; sentiment/priority consult the model **first** and fall back to the previous lexicon/keyword rules when confidence is low or models are absent — the app runs even before training
- Measured on the held-out 20%: sentiment ≈ **95.1%** test accuracy, priority ≈ **98.1%** — the sentiment model uses word + bigram features, while the priority model deliberately uses word-level features only (no phrase bigrams) so exact template phrases cannot be memorized; the near-identical train (97.9%) and test (98.1%) scores confirm no overfitting
- Admin **Sentiment × Priority** page (`/admin/analysis`): problem heatmap (category × priority), green/positive counter-matrix, and the *closed-but-still-hurting* list (Resolved + Negative + High/Medium)

#### 3. Flask App (`backend/app.py`)
- Student routes: register, login, submit complaint, view own complaints
- Admin routes: dashboard with charts, manage complaints, assign, resolve
- Auto-detects category + sentiment on complaint submission
- Sentiment priority boost applied before saving to DB
- REST API endpoints for integration

#### 4. Database (`complainify.sql`)
- MySQL via XAMPP
- Creates the `complainify` database and 7 tables: `colleges`, `users` (students + admins), `complaints` (category, sentiment, priority, assigned_to, admin_notes, ...), `otps`, `notifications`, `complaint_comments`, `audit_logs`
- Ships **without seed rows** — no users, no colleges, no complaints — so you register your own account after importing (see Setup Instructions, step 6)
- `init_db()` in `app.py` also creates `audit_logs` / `notifications` / `complaint_comments` on boot if they are missing, so a database created from an older dump keeps working

---

## Performance

| Metric | Value |
|--------|-------|
| Category model | Multinomial Naive Bayes (from scratch) |
| Category training samples | 7204 (80%) / 1806 (20%) |
| Category accuracy | ~96% |
| Sentiment dataset | 12,000 rows (claude + synth) — ground truth built in |
| Sentiment model | Multinomial NB, test accuracy ~95.1%, macro-F1 ~0.941 |
| Priority model | Multinomial NB (word-level features), test accuracy ~98.1%, macro-F1 ~0.983 |
| Rule-based sentiment baseline | Test accuracy 82.50%, macro-F1 0.840 |
| Rule-based priority baseline | Test accuracy 83.50%, macro-F1 0.820 |
| TF-IDF / sklearn / nltk | Not used — everything from scratch |

---

## Project Structure

```
Student-Complainify/
├── backend/
│   ├── app.py                    # Flask server (routes, auth, DB, ML APIs)
│   └── mcp_server.py             # MCP tools (predict, search)
├── frontend/
│   └── templates/
│       ├── admin/                # Admin pages (dashboard, complaints, training)
│       ├── student/              # Student pages (dashboard, submit)
│       └── base.html             # Shared layout
├── ml/                           # Machine-learning package (production pipeline)
│   ├── classifier.py             # MultinomialNB (from scratch) + categorize()
│   ├── sentiment.py              # ML-first sentiment engine (from-scratch rule fallback, no VADER)
│   ├── validate_data.py          # Data validation gate (before training)
│   ├── model_registry.py        # Model versioning: save/load/list latest
│   ├── retrain.py               # Full pipeline: collect → validate → append → train → version
│   ├── env.py                   # Lazy-load trained sentiment/priority models (fallback wiring)
│   ├── train_sentiment_priority.py # Train sentiment + priority NBs on data/sentiment_dataset.csv
│   ├── gen_analysis.py          # Reads MySQL → live_analysis.json (heatmaps, pink list)
│   ├── sentiment_training_log.json # Single source of truth for report/notebook metrics
│   ├── models/                   # Versioned models + manifest.json (registry)
│   └── reports/                  # Validation reports (JSON)
├── data/                         # ★ Training data + encoders
│   ├── train_dataset.csv         # Collected, labeled complaints (source of truth)
│   ├── sentiment_dataset.csv     # 12k rows, tagged sentiment + priority ground truth
│   ├── sentiment_model.json      # Trained sentiment NB
│   ├── priority_model.json        # Trained priority NB
│   ├── live_analysis.json         # Cached live heatmap snapshot (regenerated by gen_analysis.py)
│   ├── test_dataset.csv          # Held-out test set
│   ├── model_params.json         # Active model copy (back-compat)
│   └── encoders/                 # category + priority encoders/decoders
├── notebook/                      # Companion notebooks for each ML topic
├── complainify.sql               # DB schema (idempotent, no seed rows)
└── README.md
```

---

## Setup Instructions (How to Run)

> The app lives in `workspace/ComplaintMgmtSystem/` inside this repo — run every command below from that folder.

### Quick start (TL;DR)

```powershell
git clone https://github.com/Cr7Samiee/Student-Complainify.git
cd Student-Complainify/workspace/ComplaintMgmtSystem
python -m pip install -r requirements.txt
C:\xampp\mysql_start.bat
cmd /c "C:\xampp\mysql\bin\mysql.exe -u root < complainify.sql"
Copy-Item .env.example .env
python backend/app.py
# open http://127.0.0.1:5000
```

### Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.10+ | Developed and tested on 3.13.9 (Anaconda). `runtime.txt` pins 3.12.3 for the deploy host |
| XAMPP | Provides MySQL on `127.0.0.1:3306` |
| Git | |

Everything the app needs is pinned in `requirements.txt` (Flask, PyMySQL, fpdf2, python-dotenv, pytest, gunicorn). Only the notebooks need extra packages.

### 1. Clone & Install Dependencies

```powershell
git clone https://github.com/Cr7Samiee/Student-Complainify.git
cd Student-Complainify/workspace/ComplaintMgmtSystem
python -m pip install -r requirements.txt
```

Optional, if you prefer an isolated environment:

```powershell
conda create -n complaint-system python=3.10 -y
conda activate complaint-system
python -m pip install -r requirements.txt
```

Sanity-check what resolved:

```powershell
python -m pip list | Select-String 'Flask|PyMySQL|fpdf|dotenv|pytest'
```

You should see `Flask`, `PyMySQL`, **exactly one** `fpdf2`, `python-dotenv` and `pytest`. If a separate `fpdf` entry also appears, two packages are sharing the same namespace - see [Troubleshooting](#troubleshooting).

### 2. Start MySQL (XAMPP)

The bundled MySQL runs as a **manual process, not a Windows service**, so `Start-Service mysql` will not find it. Use one of:

```powershell
C:\xampp\mysql_start.bat                  # quickest
C:\xampp\mysql\bin\mysqld.exe --console   # foreground, prints startup errors
```

or open the **XAMPP Control Panel** and press **Start** next to MySQL. Confirm it is listening before continuing:

```powershell
Test-NetConnection 127.0.0.1 -Port 3306 | Select-Object TcpTestSucceeded
```

### 3. Create the Database

Run this from `workspace/ComplaintMgmtSystem/`:

```powershell
cmd /c "C:\xampp\mysql\bin\mysql.exe -u root < complainify.sql"
```

**Do not run the plain `mysql -u root < complainify.sql` form in PowerShell.** PowerShell reserves `<` for future use and fails with *"The '<' operator is reserved for future use"*; `cmd /c` hands the redirect to `cmd`, which supports it. Other options:

- **phpMyAdmin** (easiest): open `http://localhost/phpmyadmin`, go to **Import**, choose `complainify.sql`, press **Go**
- **MySQL client**: run `C:\xampp\mysql\bin\mysql.exe -u root`, then `source complainify.sql`

The script is idempotent (`CREATE DATABASE IF NOT EXISTS` / `CREATE TABLE IF NOT EXISTS`) and creates the `complainify` database itself, so you never create it by hand. It contains **no seed rows** - expect an empty database until step 6.

### 4. Configure `.env` (Optional but Recommended)

```powershell
Copy-Item .env.example .env
```

`.env` is gitignored, and `app.py` loads it from the **project root** (`workspace/ComplaintMgmtSystem/`) regardless of your working directory. Keys:

| Key | Default | Purpose |
|-----|---------|---------|
| `SECRET_KEY` | `supersecretkey` | Flask session signing - **change this** |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | `127.0.0.1`, `3306`, `root`, *(empty)*, `complainify` | MySQL connection |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` | Gmail on port 587 | Outgoing notification email |
| `RETRAIN_SCHEDULE_HOURS` | `0` (disabled) | Auto-retrain interval; `168` = weekly |
| `EMAIL_IT` ... `EMAIL_OTHER` | `admin@university.edu` | Per-category department routing |

### 5. Run the App

From `workspace/ComplaintMgmtSystem/`:

```powershell
python backend/app.py
```

Open **http://127.0.0.1:5000**. It runs with `debug=True`, so it reloads automatically when you save a file. (`cd backend` + `python app.py` works too, because the template and static folders are resolved from the file's own location rather than your current directory.)

If MySQL is not running you will see this at startup:

```
[INIT DB] (2003, "Can't connect to MySQL server on '127.0.0.1' ...")
```

That is non-fatal. The landing page, complaint form, tracker and every auth page still work; login and the dashboards fail until the database is up.

### 6. Create Your Accounts

The database is empty, so there is nothing to log in with yet:

| Role | Register at |
|------|-------------|
| Student | `http://127.0.0.1:5000/student/register` |
| Admin | `http://127.0.0.1:5000/admin/register` |

The college dropdown works even with an empty `colleges` table, because `get_colleges()` falls back to the built-in `DEFAULT_COLLEGES` list. To insert a user with SQL instead, see [Accounts](#accounts).

### 7. Run the Tests

From `workspace/ComplaintMgmtSystem/`:

```powershell
python -m pytest tests/ -q
```

| File | Needs MySQL? |
|------|--------------|
| `tests/test_classifier.py` | No |
| `tests/test_sentiment.py` | No |
| `tests/test_api.py` | Partly - `test_predict_resolution_api` and `test_similar_complaints_api` query the database |

With MySQL running the expected result is `30 passed`. With MySQL down it is `2 failed, 28 passed` - both failures are `pymysql.err.OperationalError` connection errors that disappear once step 2 is done.

### 8. (Optional) Retrain the Models

Notebooks are pre-executed, but to retrain from the CLI (from `workspace/ComplaintMgmtSystem/`):

```powershell
python ml/train_sentiment_priority.py  # retrain sentiment + priority models on data/sentiment_dataset.csv
python ml/retrain.py                   # full pipeline: collect CSV + confirmed DB rows -> validate -> train -> new model version
```

You can also trigger a retrain from the admin UI (Training page -> Retrain Model), or schedule it by setting `RETRAIN_SCHEDULE_HOURS` (e.g. `168` for weekly) in `.env` - when set, a daemon thread starts the retrain alongside the app.

### 9. (Optional) Email Notifications

Set `SMTP_USER` and `SMTP_PASS` in `.env` (step 4). Use a Gmail **App Password**, not your account password. Per-category delivery addresses come from the `EMAIL_*` keys.

Sending is skipped entirely when the credentials are empty, and every SMTP error is caught and logged, so a missing or wrong credential never blocks a complaint submission.

> **Docker?** This repo ships no `Dockerfile` / image, so there is nothing to `docker run` yet — follow the local Python steps above. The command you pasted (`docker run -d --rm --name myapp -p 3000:80 welcome:latest`) targets a generic `welcome` test image, not this Flask app (which serves on port **5000**, not 80/3000). If you want containerized deploys, say the word and I can add a `Dockerfile` + compose setup for it.

---

### Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| `[INIT DB] (2003, "Can't connect to MySQL server on '127.0.0.1' ...")` on startup | MySQL is not running - do step 2. The app still boots and serves the public pages |
| `pymysql.err.OperationalError` in tests, on login, or on any dashboard | Same cause: MySQL is down, or `complainify.sql` was never imported (steps 2-3) |
| `The '<' operator is reserved for future use` | You ran the bare `mysql ... < file` form in PowerShell - use `cmd /c` (step 3) |
| `ImportError: cannot import name 'FPDF' from 'fpdf' (unknown location)` | A partial PyFPDF uninstall deleted files that `fpdf2` shares. Repair with `python -m pip install --force-reinstall fpdf2==2.8.7` |
| `UserWarning: You have both PyFPDF & fpdf2 installed` | Two packages share the `fpdf` namespace. Keep `fpdf2` (it is what the app imports) and remove the ancient one: `python -m pip uninstall -y fpdf`. Verify afterwards with `python -c "from fpdf import FPDF; print('ok')"` - if that fails, run the repair command above |
| "Invalid credentials" straight after importing the database | Expected: the database has no users. Register first (step 6) |
| Port 5000 already in use | Another instance is still running. Find it with `Get-NetTCPConnection -LocalPort 5000 -State Listen` and stop it with `Stop-Process -Id <pid>`, or change the port in the `app.run()` call |
| `Procfile` / gunicorn fails on Windows | `gunicorn` is Linux-only and is not part of the local setup - the `Procfile` is for the deploy host. Locally use `python app.py` |
| The UI looks like an older version of the app | You may be running from the stale git worktree at `.kilo/worktrees/fragrant-beauty`, which is pinned to an old commit. Run from `backend/` in this repo and check with `git worktree list` |

---

## Accounts

Whether you can log in straight away depends on which database you are pointing at.

**A fresh import of `complainify.sql`** - the script contains no `INSERT` statements, so a newly created database has zero users. Register your own after starting the app (Setup Instructions, step 6):

| Role | Register at |
|------|-------------|
| Student | `http://127.0.0.1:5000/student/register` |
| Admin | `http://127.0.0.1:5000/admin/register` |

The college dropdown still works on a fresh database, because `get_colleges()` falls back to the built-in `DEFAULT_COLLEGES` list when the `colleges` table is empty.

**An existing development database** - the working development database already contains these pre-created accounts, and both passwords have been checked against the stored SHA-256 hashes:

| Role | Email | Password |
|------|-------|----------|
| Student | `ram@gmail.com` | `pass123` |
| Admin | `admin@complainify.edu` | `admin123` |

If login fails with "Invalid credentials" while the rest of the app is healthy, the database you are connected to simply has no user with that email - register one, or seed it with the SQL below.

### Seeding an Account with SQL

Run this in phpMyAdmin or the MySQL client. Passwords are stored as a lowercase SHA-256 hex digest by `hash_pw()`, and `plain_password` is kept only so the admin user-management page can display it:

```sql
USE complainify;
INSERT INTO users (fullname, email, phone, plain_password, password, role, college)
VALUES ('Test Student', 'test@gmail.com', '9800000000', 'test123',
        SHA2('test123', 256), 'student', 'College of Science & Technology');
```

`college` is optional (`DEFAULT NULL`) and `email` is `UNIQUE`, so re-running the same insert fails until you change the address. Note that `plain_password` is a presentation convenience only - the login check compares `hash_pw(input)` against the `password` column.

---

## Notebooks (`notebook/subfunctions/`)

Study notebooks, each focused on one ML topic and **executed** so outputs are visible:

| Notebook | Topic |
|----------|-------|
| `01_dataset_structure.ipynb` | CSV columns + category decoder |
| `02_preprocessing.ipynb` | Stopwords, stemmer, tokenizer/normalization |
| `03_train_test_split.ipynb` | Load real data + 80/20 split |
| `04_naive_bayes.ipynb` | MultinomialNB from scratch (fit/predict) |
| `05_evaluation_metrics.ipynb` | Accuracy, precision, recall, F1 on the test set |
| `06_sentiment_analysis.ipynb` | Lexicon sentiment → priority pipeline |
| `07_model_performance.ipynb` | Live `training_log.json` accuracy + per-class charts |
| `08_model_lifecycle.ipynb` | **Production data lifecycle**: validation gate → registry → versioned retraining |
| `09_sentiment_dataset_authoring.ipynb` | How the 12k sentiment/priority dataset was authored (ground truth built in) |
| `10_sentiment_priority_models.ipynb` | Train + per-class evaluation of both models vs the rule-based baseline |
| `11_live_pipeline_heatmap.ipynb` | Live MySQL heatmaps: problem matrix, green zone, closed-but-still-hurting |
| `12_accuracy_dashboard.ipynb` | **Same numbers as the admin dashboard**: category/sentiment/priority accuracy cards + correlation matrix (via `ml/model_stats.py`) |

---

## API Endpoints

### Pages

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Landing page |
| GET | `/dashboard-redirect` | Redirect to the dashboard for the session's role |
| GET | `/logout` | End session |
| GET/POST | `/submit-complaint` | Submit a complaint (auto-classify + sentiment + priority); `?anonymous=1` for an anonymous submission |
| GET/POST | `/track` | Track a complaint by ticket ID |
| GET/POST | `/forgot-password` | Request a reset OTP |
| GET/POST | `/reset-password` | Set a new password using the OTP |
| GET/POST | `/student/login`, `/student/register` | Student auth |
| GET | `/student/dashboard` | Student complaint list |
| GET | `/student/complaint/<ticket_id>` | Student complaint detail |
| GET/POST | `/student/settings` | Student profile settings |
| GET/POST | `/admin/login`, `/admin/register` | Admin auth |
| GET | `/admin/dashboard` | Admin analytics dashboard |
| GET | `/admin/complaints` | All complaints with filters |
| GET | `/admin/complaint/<ticket_id>` | Admin complaint detail |
| GET | `/admin/analysis` | Sentiment x priority heatmaps |
| GET | `/admin/report` | Reporting page |
| GET | `/admin/training-logs` | Model training history |
| GET | `/admin/audit-logs` | Audit trail |
| GET | `/admin/users` | User management |
| GET/POST | `/admin/settings` | System settings |

### Complaints & workflow (POST)

| Endpoint | Description |
|----------|-------------|
| `/admin/assign/<ticket_id>` | Assign a complaint to an admin |
| `/admin/status/<ticket_id>` | Update status (in progress / resolved) |
| `/admin/validate/<ticket_id>` | Validate an AI suggestion |
| `/admin/confirm-label/<ticket_id>` | Confirm or correct the AI label (feeds retraining) |
| `/admin/resend-email/<ticket_id>` | Re-send the department notification |
| `/admin/retrain` | Trigger a model retrain |
| `/complaint/<ticket_id>/comment` | Add a comment (student or admin) |
| `/admin/users/reset-password/<uid>` | Reset a user's password |
| `/admin/users/delete/<uid>` | Delete a user |

### ML / JSON API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/predict` | Category + confidence + tier for a text |
| POST | `/api/predict-top3` | Top-3 categories with confidence |
| POST | `/api/analyze` | Category + sentiment + priority in one call |
| GET | `/api/predict-resolution` | Predicted resolution time (queries the DB) |
| POST | `/api/similar-complaints` | Nearest existing complaints (queries the DB) |
| POST | `/api/detect-anomaly` | Anomaly check on a submission |
| GET | `/api/models`, `/api/models/latest` | Registered model versions |
| POST | `/api/retrain` | Retrain via API |

### Exports, notifications & files

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/export/pdf`, `/admin/export/csv` | Export reports |
| GET | `/admin/report/data` | Report data (JSON) |
| GET | `/notifications`, `/notifications/count` | Notification feed |
| POST | `/notifications/mark-read/<nid>`, `/notifications/mark-all-read` | Mark notifications read |
| GET | `/uploads/<filename>` | Serve an uploaded attachment |
