#!/usr/bin/env python3
"""
MySQL Restore Validator

Finds the newest backup, restores it into a test database, validates
row counts, writes a PASS/FAIL report, and optionally emails the report.
"""

from __future__ import annotations

import argparse
import gzip
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from validation import validate_database
from report import build_report, save_report, send_email_report

load_dotenv("scheduler.env")

logger = logging.getLogger("restore-validator")


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def mysql_executable() -> str:
    configured = env("MYSQL_BIN")
    if configured:
        return configured
    found = shutil.which("mysql")
    if found:
        return found
    raise FileNotFoundError(
        "MySQL client not found. Set MYSQL_BIN in scheduler.env, "
        "for example C:/Program Files/MySQL/MySQL Server 8.0/bin/mysql.exe"
    )


def mysql_base_args(mysql: str) -> list[str]:
    return [
        mysql,
        "--protocol=tcp",
        "--host", env("MYSQL_HOST", "127.0.0.1"),
        "--port", env("MYSQL_PORT", "3306"),
        "--user", env("MYSQL_USER", "root"),
    ]


def run_mysql(args: list[str], input_data=None) -> subprocess.CompletedProcess:
    mysql = mysql_executable()
    command = mysql_base_args(mysql) + args

    child_env = os.environ.copy()
    password = env("MYSQL_PASSWORD")
    if password:
        # MYSQL_PWD avoids exposing the password in the process command line.
        child_env["MYSQL_PWD"] = password

    return subprocess.run(
        command,
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=child_env,
        check=False,
    )


def find_latest_backup(backup_dir: Path) -> Path:
    candidates = [
        p for p in backup_dir.iterdir()
        if p.is_file() and (
            p.suffix.lower() in {".sql", ".gz"} or p.name.lower().endswith(".sql.gz")
        )
    ]
    if not candidates:
        raise FileNotFoundError(f"No .sql or .sql.gz backups found in {backup_dir}")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def recreate_test_database(database: str) -> None:
    if not database.replace("_", "").isalnum():
        raise ValueError("TEST_DATABASE may contain only letters, numbers, and underscores.")

    logger.info("Recreating test database: %s", database)
    result = run_mysql(["-e", f"DROP DATABASE IF EXISTS `{database}`; CREATE DATABASE `{database}`;"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="replace").strip())


def restore_backup(backup: Path, database: str) -> None:
    logger.info("Restoring backup: %s", backup.name)

    if backup.name.lower().endswith(".gz"):
        with gzip.open(backup, "rb") as source:
            result = run_mysql(["--database", database], input_data=source.read())
    else:
        with backup.open("rb") as source:
            result = run_mysql(["--database", database], input_data=source.read())

    if result.returncode != 0:
        raise RuntimeError(
            "Restore failed: " + result.stderr.decode(errors="replace").strip()
        )


def configure_logging() -> None:
    level = getattr(logging, env("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def run_once() -> int:
    started = datetime.now()
    backup_dir = Path(env("BACKUP_DIR", "./backups"))
    report_dir = Path(env("REPORT_DIR", "./reports"))
    test_db = env("TEST_DATABASE", "restore_validation_test")

    report_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup = None
    validation_results = []
    restore_ok = False
    error = None

    try:
        backup = find_latest_backup(backup_dir)
        recreate_test_database(test_db)
        restore_backup(backup, test_db)
        restore_ok = True
        validation_results = validate_database(
            run_mysql=run_mysql,
            database=test_db,
            expected_counts=env("EXPECTED_COUNTS"),
        )
    except Exception as exc:
        error = str(exc)
        logger.exception("Validation run failed")

    passed = restore_ok and bool(validation_results) and all(
        item["passed"] for item in validation_results
    )

    report = build_report(
        started=started,
        backup=backup,
        database=test_db,
        restore_ok=restore_ok,
        validation_results=validation_results,
        passed=passed,
        error=error,
    )

    report_path = save_report(report, report_dir)
    logger.info("Report written to %s", report_path)

    if env("SMTP_HOST"):
        try:
            send_email_report(
                report=report,
                subject=f"MySQL Restore Validation: {'PASS' if passed else 'FAIL'}",
            )
            logger.info("Email report sent")
        except Exception:
            logger.exception("Could not send email report")

    print(report)
    return 0 if passed else 1


def main() -> int:
    configure_logging()

    parser = argparse.ArgumentParser(
        description="Restore the latest MySQL backup and validate it."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one restore/validation cycle immediately.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="Repeat every N seconds. Use 0 for a single run.",
    )
    args = parser.parse_args()

    if args.interval <= 0:
        return run_once()

    logger.info("Scheduler started; interval=%s seconds", args.interval)
    while True:
        code = run_once()
        logger.info("Cycle completed with exit code %s", code)
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
