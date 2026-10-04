# MySQL Restore Validator

A Python automation project that finds the latest MySQL backup, restores it into a temporary test database, runs validation queries, and produces a PASS/FAIL report.

## Features

- Automatically identifies the newest `.sql` or `.sql.gz` backup
- Restores the backup with the MySQL command-line client via Python `subprocess`
- Uses a separate test database so the source database is not overwritten
- Runs `COUNT(*)` validation checks on configured tables
- Produces timestamped validation reports
- Returns exit code `0` for PASS and `1` for FAIL
- Optional SMTP email reporting
- Supports one-shot execution or a simple recurring scheduler
- Keeps passwords out of the command line by using environment variables

## Project structure

```text
mysql-restore-validator/
├── restore_scheduler.py
├── validation.py
├── report.py
├── scheduler.env.example
├── requirements.txt
├── README.md
├── .gitignore
├── backups/
│   └── .gitkeep
└── reports/
    └── .gitkeep
```

## Requirements

- Python 3.10+
- MySQL Server / MySQL client
- A MySQL `.sql` or `.sql.gz` backup
- Permission to create and drop the test database

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/Scripts/activate
```

On Windows CMD:

```cmd
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create the environment file

```bash
cp scheduler.env.example scheduler.env
```

Edit `scheduler.env` and set your MySQL password and backup settings.

For a normal MySQL 8.0 Windows installation:

```text
MYSQL_BIN=C:/Program Files/MySQL/MySQL Server 8.0/bin/mysql.exe
```

The project deliberately does not store the real password in Git.

## Validation configuration

For example:

```text
EXPECTED_COUNTS=students=3
```

Multiple tables can be checked:

```text
EXPECTED_COUNTS=students=3,orders=10
```

The validator runs queries equivalent to:

```sql
SELECT COUNT(*) FROM students;
SELECT COUNT(*) FROM orders;
```

## Run once

```bash
python restore_scheduler.py --once
```

A successful run looks like:

```text
============================================================
MYSQL BACKUP RESTORE VALIDATION
============================================================
Run time: 2026-10-04 17:30:00
Backup: backup_20261004_170000.sql
Test database: restore_validation_test
Restore: PASS

VALIDATION CHECKS
------------------------------------------------------------
PASS | students | expected=3 | actual=3

============================================================
FINAL RESULT: PASS
============================================================
```

A report is saved under `reports/`.

## Run on an interval

For a simple demonstration scheduler:

```bash
python restore_scheduler.py --interval 3600
```

This executes one cycle every hour.

For production scheduling, Windows Task Scheduler, cron, or a CI/CD scheduler can invoke:

```bash
python restore_scheduler.py --once
```

## Optional email reporting

Configure SMTP values in `scheduler.env`:

```text
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_email@example.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@example.com
EMAIL_TO=recipient@example.com
```

Email is optional. The local report is always generated.

## Safety

The script restores into:

```text
restore_validation_test
```

It does not restore over the original production/source database.

The test database is recreated before each validation cycle.

Never commit `scheduler.env`, real passwords, production backups, or email credentials.

## Suggested demo

1. Put a known-good `.sql` backup into `backups/`.
2. Set `EXPECTED_COUNTS` to match the backup.
3. Run `python restore_scheduler.py --once`.
4. Capture the terminal output showing `FINAL RESULT: PASS`.
5. Open the generated report in `reports/`.
6. Commit the source code and README, but keep credentials and real backups out of Git.

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | Restore and all validation checks passed |
| 1 | Restore failed or one/more validation checks failed |

## Skills demonstrated

- Python automation
- MySQL administration
- Backup and restore validation
- `subprocess`
- Environment-based configuration
- SQL validation queries
- Logging
- SMTP reporting
- Scheduling
- Failure handling
