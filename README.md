# Student Academic Performance Management and Prediction System

A Python backend portfolio project for managing students, attendance, examination marks, academic reports, and educational machine-learning predictions.

**Stack:** Python 3.12, FastAPI, SQLAlchemy, MySQL 8.4, Pandas, NumPy, scikit-learn, JWT, Argon2, pytest, Docker, GitHub Actions.

## Features

- Registration and login with Argon2 password hashing and expiring JWTs.
- Account-level authorization: users can only access their own students, subjects and academic records.
- Student and subject CRUD, pagination, uniqueness constraints and input validation.
- Attendance counts and per-subject, per-term internal, assignment and examination marks.
- Attendance percentages, subject/overall averages, and term trends using Pandas.
- Logistic Regression and Random Forest comparison with validation-based selection and held-out test evaluation.
- Direct-feature predictions and predictions from saved student records.
- SQLite for local practice; MySQL in Docker Compose and CI integration tests.
- Swagger documentation, automated tests and a repeatable HTTP demo.

This implements **Project 1** from the assignment. The separate AWS/EKS/Terraform project is not included. Swagger is the interactive interface for this backend project.

## Quick start: Windows PowerShell

```powershell
git clone https://github.com/Yayathi0503/student-performance-system.git
cd student-performance-system
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/setup_local.py
.\.venv\Scripts\python.exe -m ml.train_model
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs. Keep the terminal running; Ctrl+C stops it.
If venv reports an `ensurepip` error, use `python -m pip --python .venv\Scripts\python.exe install -r requirements.txt`.
On Linux/macOS, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.

`setup_local.py` generates random secrets once and preserves an existing `.env`.
Local data is saved to `performance.db`. The earlier milestone's `students.db` is preserved; it is not imported because those records have no owning account.

## MySQL and Docker

Start Docker Desktop with Linux containers, then run from this folder:

```powershell
python scripts/setup_local.py
docker compose up --build -d --wait
docker compose ps
```

Open http://127.0.0.1:8000/docs. Stop an existing local API first if port 8000 is occupied.
The image trains the demonstration model during build. MySQL uses a persistent named volume and has no published host port. The API binds to localhost.

```powershell
docker compose logs api
docker compose down
```

`down` preserves database data. Adding `--volumes` erases it. Generated database passwords are URL-safe hexadecimal strings, suitable for the supplied connection string.

## Try the complete flow

1. Call `POST /auth/register` with an email and a password of at least 10 characters.
2. Click **Authorize** in `/docs`. Enter your email in **username** and your password. Leave client ID/secret blank.
3. Call `POST /students`:

```json
{"registration_number":"CS001","name":"Asha","department":"Computer Science","semester":1,"email":"asha@example.com"}
```

4. Call `POST /subjects`: `{"code":"PY101","name":"Python"}`.
5. Use the returned student and subject IDs in `POST /attendance`:

```json
{"student_id":1,"subject_id":1,"date":"2026-01-01","attended":18,"total":20}
```

6. Call `POST /academic-records`:

```json
{"student_id":1,"subject_id":1,"term":1,"internal_marks":75,"assignment_score":80,"exam_marks":85}
```

7. Call `GET /reports/1` and `GET /predictions/1`, replacing 1 with your actual student ID.

For an automated walkthrough, run in a second terminal:

```powershell
.\.venv\Scripts\python.exe scripts/demo.py
```

This registers a unique fictional account, logs in, creates academic records, verifies the report and prediction, then removes the fictional student and subject. The demo account remains.

## Endpoints

- Public: `GET /`, `GET /health`, `POST /auth/register`, `POST /auth/login`.
- Identity: `GET /auth/me`.
- Students: `POST/GET /students`, `GET/PUT/DELETE /students/{id}`.
- Subjects: `POST/GET /subjects`, `GET/PUT/DELETE /subjects/{id}`.
- Attendance: `POST /attendance`, `GET /attendance?student_id={id}`, `PUT/DELETE /attendance/{id}`.
- Marks: `POST /academic-records`, `GET /academic-records?student_id={id}`, `PUT/DELETE /academic-records/{id}`.
- Reports: `GET /reports/{student_id}`.
- Predictions: `POST /predict`, `GET /predictions/{student_id}`.

All nonpublic routes require a Bearer token. Errors: 401 for invalid/missing tokens, 404 for missing/foreign-owned records, 409 for duplicates/conflicts, 422 for invalid input, 503 for an unavailable model. PUT expects the full resource body.

## Architecture

Requests pass through Pydantic validation, JWT authentication and ownership checks, then SQLAlchemy sessions. The database enforces relationships and uniqueness; Pandas summarizes academic data; a trusted model artifact serves predictions.

- `app/main.py`: app factory, startup, health and router registration.
- `app/config.py`, `app/database.py`, `app/models.py`: settings, sessions, relational schema.
- `app/security.py`, `app/routes/auth.py`: hashing, tokens and login.
- `app/routes/students.py`, `app/routes/academics.py`: ownership-aware CRUD.
- `app/services/analytics.py`: report calculations.
- `app/services/prediction.py`, `app/routes/reports.py`: model loading, reports and predictions.
- `ml/train_model.py`, `ml/evaluate_model.py`: reproducible training/evaluation.
- `tests/`: API, authorization, database constraints and model tests.
- `.github/workflows/ci.yml`: SQLite/MySQL tests, model evaluation, Docker build and HTTP demo.

Each student/subject has one owner. Student registration numbers and emails are unique per owner. Records cannot link across owners. Attendance permits one aggregate per student/subject/date. Marks permit one record per student/subject/term. Student deletion cascades academic rows; referenced subjects cannot be deleted.

Attendance is total attended / total scheduled classes × 100. Each academic row equally averages its three score components. Overall/subject averages weight each recorded subject-term equally. Trends compare the latest two recorded terms. Empty reports return null values. Predictions use all recorded attendance and the latest term's average internal and assignment scores.

Startup creates missing tables but does not migrate existing ones. Use versioned migrations before changing a populated production schema.

## Machine learning

```powershell
.\.venv\Scripts\python.exe -m ml.train_model
.\.venv\Scripts\python.exe -m ml.evaluate_model
```

Training creates 2,000 synthetic records using a fixed seed. Features are attendance, internal marks and assignment scores, all 0–100. The outcome is a simulated weighted score plus random noise thresholded at 50, not an observed educational outcome.

Stratified splits are 60% train, 20% validation and 20% test. Logistic Regression's scaler fits only training data. The highest validation F1 selects between Logistic Regression and Random Forest. Only after selection are test metrics computed. `artifacts/metrics.json` reports accuracy, precision, recall, F1 and confusion matrices for both models. Matrix rows are actual labels and columns are predictions, ordered `[0, 1]`.

Generated artifacts are excluded from Git and recreated by training. Load only trusted joblib files; this format can execute code. Predictions are educational demonstrations, not validated real-student recommendations. Real deployment requires appropriate data consent, independent evaluation, fairness checks and human review.

## Verification

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use isolated temporary SQLite databases. To test MySQL, set `TEST_DATABASE_URL` to a dedicated disposable database. **Tests drop and recreate its tables; never point this variable at real application data.** CI provisions its own disposable MySQL service.

GitHub Actions runs tests on every push/PR, uploads model metrics, and builds/smoke-tests the container. Uploading a repository does not host a public API; Docker serves it locally or on a configured server.

## Configuration and deployment

See `.env.example`. JWT_SECRET requires 32+ characters and rejects placeholder values. Tokens expire after 30 minutes by default. Secrets, databases, environments and model binaries are excluded from Git and Docker's build context.

This is a local portfolio deployment. Before public exposure, configure HTTPS, login/register rate limits, controlled registration, backups, migrations and secret management. Accounts are independent owners; institution-wide administrator/teacher/student roles and SSO are not implemented.

## Learning path

Follow a request through `schemas.py`, `routes/students.py` and `models.py`. Then study authentication, academic records, report formulas and model training. A useful first extension is student search, with a test proving searches only return the signed-in account's students.
