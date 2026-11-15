#!/usr/bin/env python3
"""Profiling tệp Parquet cục bộ và tạo báo cáo gọn, có thể tái lập."""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def quote_identifier(value: str) -> str:
    """Đặt dấu nháy cho định danh DuckDB, kể cả khi có dấu nháy kép bên trong."""
    return '"' + value.replace('"', '""') + '"'


def sql_literal(value: str) -> str:
    """Đặt dấu nháy cho chuỗi literal trong SQL."""
    return "'" + value.replace("'", "''") + "'"


def resolve_inputs(value: str) -> list[Path]:
    """Tìm tệp Parquet cục bộ từ tệp, thư mục hoặc glob; từ chối URL từ xa."""
    if "://" in value:
        raise ValueError(
            "Chỉ chấp nhận đầu vào Parquet cục bộ; hãy thu thập nguồn qua quy trình riêng."
        )

    candidate = Path(value).expanduser()
    if candidate.is_file():
        matches = [candidate]
    elif candidate.is_dir():
        matches = [
            *candidate.rglob("*.parquet"),
            *candidate.rglob("*.geoparquet"),
        ]
    else:
        matches = [Path(item) for item in glob.glob(value, recursive=True)]

    parquet_suffixes = {".parquet", ".geoparquet"}
    files = sorted(
        {
            item.resolve()
            for item in matches
            if item.is_file() and item.suffix.lower() in parquet_suffixes
        }
    )
    if not files:
        raise ValueError(f"Không tìm thấy tệp .parquet cục bộ cho đầu vào: {value}")
    return files


def is_list_type(data_type: str) -> bool:
    normalized = data_type.strip().upper()
    return normalized.endswith("[]") or normalized.startswith("LIST(")


def is_string_type(data_type: str) -> bool:
    normalized = data_type.strip().upper()
    if is_list_type(normalized):
        return False
    return normalized.startswith(("VARCHAR", "CHAR", "TEXT", "STRING"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_expression(files: list[Path]) -> str:
    paths = ", ".join(sql_literal(path.as_posix()) for path in files)
    return f"read_parquet([{paths}], union_by_name=true)"


def profile_files(
    files: list[Path],
    output_dir: Path,
    input_label: str,
    hash_inputs: bool = False,
) -> dict[str, Any]:
    try:
        import duckdb
    except ImportError as exc:
        raise RuntimeError(
            "Chưa cài DuckDB. Chạy lệnh: python -m pip install -r requirements.txt"
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(database=":memory:")
    try:
        read_expression = _read_expression(files)
        connection.execute(f"CREATE VIEW source_data AS SELECT * FROM {read_expression}")
        schema_rows = connection.execute("DESCRIBE source_data").fetchall()
        row_count = connection.execute("SELECT COUNT(*) FROM source_data").fetchone()[0]

        aggregate_expressions = ["COUNT(*) AS total_rows"]
        metric_aliases: list[dict[str, str | None]] = []
        for index, schema_row in enumerate(schema_rows):
            column_name, data_type = str(schema_row[0]), str(schema_row[1])
            identifier = quote_identifier(column_name)
            aliases: dict[str, str | None] = {
                "null": f"null_{index}",
                "empty": None,
                "blank": None,
            }
            aggregate_expressions.append(
                f"COUNTIF({identifier} IS NULL) AS {aliases['null']}"
            )

            if is_list_type(data_type):
                aliases["empty"] = f"empty_{index}"
                aggregate_expressions.append(
                    "COUNTIF("
                    f"{identifier} IS NOT NULL AND COALESCE(array_length({identifier}), 0) = 0"
                    f") AS {aliases['empty']}"
                )
            if is_string_type(data_type):
                aliases["blank"] = f"blank_{index}"
                aggregate_expressions.append(
                    "COUNTIF("
                    f"{identifier} IS NOT NULL AND TRIM({identifier}) = ''"
                    f") AS {aliases['blank']}"
                )
            metric_aliases.append(aliases)

        metrics = connection.execute(
            "SELECT " + ", ".join(aggregate_expressions) + " FROM source_data"
        ).fetchone()
        result_columns = [item[0] for item in connection.description]
        metric_by_name = dict(zip(result_columns, metrics))

        profile_path = output_dir / "column_profile.csv"
        with profile_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=[
                    "column",
                    "data_type",
                    "row_count",
                    "null_count",
                    "null_pct",
                    "empty_list_count",
                    "empty_list_pct",
                    "blank_string_count",
                    "blank_string_pct",
                ],
            )
            writer.writeheader()
            for index, schema_row in enumerate(schema_rows):
                column_name, data_type = str(schema_row[0]), str(schema_row[1])
                aliases = metric_aliases[index]
                null_count = int(metric_by_name[aliases["null"]] or 0)
                empty_count = (
                    int(metric_by_name[aliases["empty"]] or 0)
                    if aliases["empty"]
                    else None
                )
                blank_count = (
                    int(metric_by_name[aliases["blank"]] or 0)
                    if aliases["blank"]
                    else None
                )
                writer.writerow(
                    {
                        "column": column_name,
                        "data_type": data_type,
                        "row_count": row_count,
                        "null_count": null_count,
                        "null_pct": _percentage(null_count, row_count),
                        "empty_list_count": empty_count,
                        "empty_list_pct": _percentage(empty_count, row_count),
                        "blank_string_count": blank_count,
                        "blank_string_pct": _percentage(blank_count, row_count),
                    }
                )

        manifest = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "tool_version": "0.1.0",
            "input_label": input_label,
            "row_count": int(row_count),
            "input_files": [
                {
                    "name": path.name,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path) if hash_inputs else None,
                }
                for path in files
            ],
            "schema": [
                {"column": str(row[0]), "data_type": str(row[1])}
                for row in schema_rows
            ],
            "reports": ["column_profile.csv"],
            "hash_inputs_requested": hash_inputs,
        }
        (output_dir / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return manifest
    finally:
        connection.close()


def _percentage(count: int | None, total: int) -> str:
    if count is None or total == 0:
        return ""
    return f"{100.0 * count / total:.3f}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Profiling schema Parquet cục bộ, giá trị null, chuỗi trắng và danh sách rỗng."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Tệp Parquet cục bộ, thư mục hoặc mẫu glob.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Thư mục lưu các báo cáo gọn.",
    )
    parser.add_argument(
        "--label",
        default="ban-chup-cuc-bo-chua-gan-nhan",
        help="Nhãn nguồn/phiên bản dễ đọc, được ghi vào manifest của lần chạy.",
    )
    parser.add_argument(
        "--hash-inputs",
        action="store_true",
        help="Tính SHA-256 cho mỗi tệp đầu vào; thao tác này đọc toàn bộ mỗi tệp một lần.",
    )
    return parser


def configure_console_encoding() -> None:
    """Đảm bảo thông báo tiếng Việt ghi được ra console trên Windows."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    configure_console_encoding()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        files = resolve_inputs(args.input)
        manifest = profile_files(files, args.output, args.label, args.hash_inputs)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    print(
        f"Đã profiling {manifest['row_count']:,} dòng từ {len(files)} tệp Parquet. "
        f"Báo cáo: {args.output.resolve()}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
