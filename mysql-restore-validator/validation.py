"""Database validation helpers."""

from __future__ import annotations

from typing import Callable


def parse_expected_counts(value: str) -> dict[str, int]:
    """
    Parse:
        students=3,orders=10
    into:
        {"students": 3, "orders": 10}
    """
    result: dict[str, int] = {}
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError(
                f"Invalid EXPECTED_COUNTS entry '{item}'. Use table=count."
            )
        table, count = item.split("=", 1)
        table = table.strip()
        if not table.replace("_", "").isalnum():
            raise ValueError(f"Invalid table name: {table}")
        result[table] = int(count.strip())
    return result


def validate_database(
    run_mysql: Callable,
    database: str,
    expected_counts: str,
) -> list[dict]:
    checks = parse_expected_counts(expected_counts)
    if not checks:
        raise ValueError(
            "EXPECTED_COUNTS is empty. Add entries such as students=3."
        )

    results = []
    for table, expected in checks.items():
        query = f"SELECT COUNT(*) FROM `{table}`;"
        result = run_mysql(["--database", database, "--batch", "--skip-column-names", "-e", query])

        if result.returncode != 0:
            results.append({
                "table": table,
                "expected": expected,
                "actual": None,
                "passed": False,
                "error": result.stderr.decode(errors="replace").strip(),
            })
            continue

        raw = result.stdout.decode(errors="replace").strip()
        try:
            actual = int(raw)
        except ValueError:
            actual = None

        results.append({
            "table": table,
            "expected": expected,
            "actual": actual,
            "passed": actual == expected,
            "error": "",
        })

    return results
