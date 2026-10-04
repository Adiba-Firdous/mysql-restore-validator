"""Report generation and optional SMTP delivery."""

from __future__ import annotations

import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path


def build_report(
    started: datetime,
    backup,
    database: str,
    restore_ok: bool,
    validation_results: list[dict],
    passed: bool,
    error: str | None,
) -> str:
    lines = [
        "=" * 60,
        "MYSQL BACKUP RESTORE VALIDATION",
        "=" * 60,
        f"Run time: {started.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Backup: {backup.name if backup else 'N/A'}",
        f"Test database: {database}",
        f"Restore: {'PASS' if restore_ok else 'FAIL'}",
        "",
        "VALIDATION CHECKS",
        "-" * 60,
    ]

    if validation_results:
        for item in validation_results:
            status = "PASS" if item["passed"] else "FAIL"
            actual = item["actual"] if item["actual"] is not None else "ERROR"
            lines.append(
                f"{status:4} | {item['table']} | expected={item['expected']} | actual={actual}"
            )
            if item.get("error"):
                lines.append(f"      error: {item['error']}")
    else:
        lines.append("No validation checks completed.")

    if error:
        lines.extend(["", f"ERROR: {error}"])

    lines.extend([
        "",
        "=" * 60,
        f"FINAL RESULT: {'PASS' if passed else 'FAIL'}",
        "=" * 60,
    ])
    return "\n".join(lines)


def save_report(report: str, report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    filename = f"restore_report_{datetime.now():%Y%m%d_%H%M%S}.txt"
    path = report_dir / filename
    path.write_text(report + "\n", encoding="utf-8")
    return path


def send_email_report(report: str, subject: str) -> None:
    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("EMAIL_FROM", username).strip()
    recipient = os.getenv("EMAIL_TO", "").strip()

    if not host or not recipient:
        raise ValueError("SMTP_HOST and EMAIL_TO are required for email delivery.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(report)

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        if username:
            smtp.login(username, password)
        smtp.send_message(message)
