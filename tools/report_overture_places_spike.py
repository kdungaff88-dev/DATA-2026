#!/usr/bin/env python3
"""Tạo báo cáo tổng hợp DuckDB cho Mini Data Spike Overture Places Hoa Kỳ."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

try:
    from tools.profile_parquet import (
        is_list_type,
        is_string_type,
        profile_files,
        quote_identifier,
        resolve_inputs,
        sql_literal,
    )
except ModuleNotFoundError as exc:
    if exc.name != "tools":
        raise
    from profile_parquet import (  # type: ignore[no-redef]
        is_list_type,
        is_string_type,
        profile_files,
        quote_identifier,
        resolve_inputs,
        sql_literal,
    )


FIELD_CANDIDATES = (
    ("id", "id"),
    ("geometry", "geometry"),
    ("name_primary", "names.primary"),
    ("category_primary", "taxonomy.primary"),
    ("category_alternates", "taxonomy.alternates"),
    ("taxonomy_hierarchy", "taxonomy.hierarchy"),
    ("basic_category", "basic_category"),
    ("addresses", "addresses"),
    ("websites", "websites"),
    ("phones", "phones"),
    ("emails", "emails"),
    ("socials", "socials"),
    ("confidence", "confidence"),
    ("operating_status", "operating_status"),
    ("operating_status_value", "operating_status.value"),
    ("sources", "sources"),
    ("brand", "brand"),
    ("brand_name_primary", "brand.names.primary"),
    ("update_time", "update_time"),
)
CONTACT_FIELDS = ("addresses", "websites", "phones", "emails")
FILTERED_STRING_LIST_FIELDS = {
    "websites",
    "phones",
    "emails",
    "socials",
    "category_alternates",
    "taxonomy_hierarchy",
}
LIST_STRUCT_FIELDS = (
    ("address_freeform", "addresses", "freeform", True),
    ("address_locality", "addresses", "locality", True),
    ("address_postcode", "addresses", "postcode", True),
    ("address_region", "addresses", "region", True),
    ("address_country", "addresses", "country", True),
    ("source_dataset", "sources", "dataset", True),
    ("source_license", "sources", "license", True),
    ("source_provider", "sources", "provider", True),
    ("source_record_id", "sources", "record_id", True),
    ("source_update_time", "sources", "update_time", True),
    ("source_confidence", "sources", "confidence", False),
)
FIELD_DISPLAY_PATHS = {
    "category_alternates": "taxonomy.alternates",
    "taxonomy_hierarchy": "taxonomy.hierarchy",
    "websites": "websites",
    "phones": "phones",
    "emails": "emails",
    "socials": "socials",
    "address_freeform": "addresses[*].freeform",
    "address_locality": "addresses[*].locality",
    "address_postcode": "addresses[*].postcode",
    "address_region": "addresses[*].region",
    "address_country": "addresses[*].country",
    "source_dataset": "sources[*].dataset",
    "source_license": "sources[*].license",
    "source_provider": "sources[*].provider",
    "source_record_id": "sources[*].record_id",
    "source_update_time": "sources[*].update_time",
    "source_confidence": "sources[*].confidence",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _field_expression(path: str) -> str:
    return ".".join(quote_identifier(part) for part in path.split("."))


def _describe_expression(connection: Any, expression: str) -> str | None:
    try:
        row = connection.execute(
            f"DESCRIBE SELECT {expression} AS value FROM source_data"
        ).fetchone()
    except Exception:
        return None
    return str(row[1]) if row else None


def _present_predicate(expression: str, data_type: str) -> tuple[str, str]:
    if is_list_type(data_type):
        return (
            f"{expression} IS NOT NULL AND COALESCE(array_length({expression}), 0) > 0",
            "List không null và có ít nhất một phần tử.",
        )
    if is_string_type(data_type):
        return (
            f"{expression} IS NOT NULL AND TRIM({expression}) <> ''",
            "Chuỗi không null và không rỗng sau TRIM.",
        )
    return f"{expression} IS NOT NULL", "Giá trị không null."


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _pct(count: int | None, total: int) -> str:
    if count is None or not total:
        return ""
    return f"{100.0 * count / total:.3f}"


def _find_run_manifest(input_path: Path) -> Path:
    directory = input_path if input_path.is_dir() else input_path.parent
    for parent in (directory, *directory.parents):
        candidate = parent / "run_manifest.json"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("Không tìm thấy run_manifest.json của downloader.")


def _find_type_manifest(input_path: Path) -> Path:
    directory = input_path if input_path.is_dir() else input_path.parent
    candidate = directory / "manifest.json"
    if not candidate.is_file():
        raise FileNotFoundError("Không tìm thấy manifest.json của feature type.")
    return candidate


def _make_view(connection: Any, files: list[Path]) -> None:
    paths = ", ".join(sql_literal(path.as_posix()) for path in files)
    connection.execute(
        "CREATE VIEW source_data AS "
        f"SELECT * FROM read_parquet([{paths}], union_by_name=true)"
    )


def _profile_geometry(files: list[Path], batch_size: int = 100_000) -> dict[str, Any]:
    try:
        import pyarrow.parquet as parquet
        import shapely
    except ImportError as exc:
        return {
            "status": "not_measured",
            "reason": f"Thiếu PyArrow hoặc Shapely: {exc}",
        }

    totals = {
        "row_count": 0,
        "null_count": 0,
        "unparseable_wkb_count": 0,
        "valid_count": 0,
        "invalid_count": 0,
        "empty_count": 0,
    }
    try:
        for path in files:
            parquet_file = parquet.ParquetFile(path)
            if "geometry" not in parquet_file.schema_arrow.names:
                return {
                    "status": "not_available",
                    "reason": "Schema không có geometry.",
                }
            for batch in parquet_file.iter_batches(
                columns=["geometry"], batch_size=batch_size
            ):
                values = batch.column(0).to_pylist()
                geometries = shapely.from_wkb(values, on_invalid="ignore")
                valid = shapely.is_valid(geometries)
                empty = shapely.is_empty(geometries)
                totals["row_count"] += len(values)
                for value, geometry, is_valid, is_empty in zip(
                    values, geometries, valid, empty
                ):
                    if value is None:
                        totals["null_count"] += 1
                    elif geometry is None:
                        totals["unparseable_wkb_count"] += 1
                    elif bool(is_valid):
                        totals["valid_count"] += 1
                        totals["empty_count"] += int(bool(is_empty))
                    else:
                        totals["invalid_count"] += 1
    except Exception as exc:
        return {
            "status": "failed",
            "reason": f"{type(exc).__name__}: {str(exc)[:500]}",
            **totals,
        }

    nonnull_count = totals["row_count"] - totals["null_count"]
    totals.update(
        {
            "status": "completed",
            "method": f"Shapely {shapely.__version__}; PyArrow batches of {batch_size:,}",
            "valid_pct_nonnull": _pct(totals["valid_count"], nonnull_count),
        }
    )
    return totals


def _category_profile(
    connection: Any,
    category_expression: str,
    fields: dict[str, tuple[str, str, str]],
    row_count: int,
    output_path: Path,
) -> list[dict[str, Any]]:
    aliases: list[tuple[str, str, str]] = []
    expressions = [
        f"CAST({category_expression} AS VARCHAR) AS category",
        "COUNT(*) AS row_count",
    ]
    for name in CONTACT_FIELDS + ("confidence",):
        if name not in fields:
            continue
        expression, data_type, _ = fields[name]
        predicate, _definition = _present_predicate(expression, data_type)
        alias = f"available_{name}"
        expressions.append(f"COUNTIF({predicate}) AS {alias}")
        aliases.append((name, alias, expression))

    query = (
        "SELECT "
        + ", ".join(expressions)
        + " FROM source_data GROUP BY 1 ORDER BY row_count DESC LIMIT 100"
    )
    raw_rows = connection.execute(query).fetchall()
    rows = []
    for raw in raw_rows:
        category = raw[0] if raw[0] is not None else "(không có category chính)"
        row: dict[str, Any] = {
            "category_primary": category,
            "row_count": int(raw[1]),
            "share_of_dataset_pct": _pct(int(raw[1]), row_count),
        }
        for index, (name, _alias, _expression) in enumerate(aliases, start=2):
            count = int(raw[index] or 0)
            row[f"{name}_available_count"] = count
            row[f"{name}_available_pct"] = _pct(count, int(raw[1]))
        rows.append(row)

    columns = ["category_primary", "row_count", "share_of_dataset_pct"]
    for name, _alias, _expression in aliases:
        columns.extend([f"{name}_available_count", f"{name}_available_pct"])
    _write_csv(output_path, columns, rows)
    return rows


def generate_report(
    input_value: str,
    output_dir: Path,
    label: str,
    run_manifest_path: Path | None = None,
    type_manifest_path: Path | None = None,
) -> dict[str, Any]:
    try:
        import duckdb
    except ImportError as exc:
        raise RuntimeError(
            "Chưa cài DuckDB. Chạy lệnh: python -m pip install -r requirements.txt"
        ) from exc

    files = resolve_inputs(input_value)
    input_path = Path(input_value).expanduser()
    run_manifest_path = run_manifest_path or _find_run_manifest(input_path)
    type_manifest_path = type_manifest_path or _find_type_manifest(input_path)
    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    type_manifest = json.loads(type_manifest_path.read_text(encoding="utf-8"))
    if run_manifest.get("status") != "completed":
        raise ValueError("Run manifest downloader chưa có trạng thái completed.")
    if type_manifest.get("status") != "completed":
        raise ValueError("Manifest feature type chưa có trạng thái completed.")

    output_dir.mkdir(parents=True, exist_ok=True)
    profile_dir = output_dir / "profile"
    profile_manifest = profile_files(files, profile_dir, label, hash_inputs=False)

    connection = duckdb.connect(database=":memory:")
    try:
        _make_view(connection, files)
        schema_rows = connection.execute("DESCRIBE source_data").fetchall()
        schema = {str(row[0]): str(row[1]) for row in schema_rows}
        row_count = int(
            connection.execute("SELECT COUNT(*) FROM source_data").fetchone()[0]
        )

        fields: dict[str, tuple[str, str, str]] = {}
        for metric_name, path in FIELD_CANDIDATES:
            root_column = path.split(".")[0]
            if root_column not in schema:
                continue
            expression = _field_expression(path)
            if metric_name in FILTERED_STRING_LIST_FIELDS:
                expression = (
                    f"list_filter({expression}, lambda item: "
                    "item IS NOT NULL AND TRIM(item) <> '')"
                )
            data_type = _describe_expression(connection, expression)
            if data_type:
                _predicate, definition = _present_predicate(expression, data_type)
                if metric_name in FILTERED_STRING_LIST_FIELDS:
                    definition = (
                        "List có ít nhất một chuỗi không null và không trắng; "
                        "lọc phần tử trong DuckDB."
                    )
                fields[metric_name] = (expression, data_type, definition)

        if "category_primary" not in fields:
            for path in ("categories.primary", "basic_category"):
                root_column = path.split(".")[0]
                if root_column not in schema:
                    continue
                expression = _field_expression(path)
                data_type = _describe_expression(connection, expression)
                if data_type:
                    _predicate, definition = _present_predicate(expression, data_type)
                    fields["category_primary"] = (
                        expression,
                        data_type,
                        definition,
                    )
                    break
        if "category_alternates" not in fields:
            path = "categories.alternate"
            if path.split(".")[0] in schema:
                expression = _field_expression(path)
                data_type = _describe_expression(connection, expression)
                if data_type:
                    _predicate, definition = _present_predicate(expression, data_type)
                    fields["category_alternates"] = (
                        expression,
                        data_type,
                        definition,
                    )

        for metric_name, root_column, member, is_string in LIST_STRUCT_FIELDS:
            if root_column not in schema:
                continue
            member_expression = f"item.{quote_identifier(member)}"
            condition = f"{member_expression} IS NOT NULL"
            if is_string:
                condition += f" AND TRIM({member_expression}) <> ''"
            expression = (
                f"list_filter({quote_identifier(root_column)}, "
                f"lambda item: {condition})"
            )
            data_type = _describe_expression(connection, expression)
            if data_type:
                fields[metric_name] = (
                    expression,
                    data_type,
                    f"Ít nhất một phần tử có {member} không null"
                    + (" và không trắng." if is_string else "."),
                )

        select_expressions = ["COUNT(*) AS total_rows"]
        metric_aliases: dict[str, str] = {}
        for index, (name, (expression, data_type, _definition)) in enumerate(
            fields.items()
        ):
            predicate, _definition = _present_predicate(expression, data_type)
            alias = f"field_{index}"
            select_expressions.append(f"COUNTIF({predicate}) AS {alias}")
            metric_aliases[name] = alias

        if "id" in fields:
            id_expression = fields["id"][0]
            select_expressions.extend(
                [
                    f"COUNT(DISTINCT {id_expression}) AS distinct_ids",
                    f"COUNTIF({id_expression} IS NULL) AS null_ids",
                    f"(COUNT({id_expression}) - COUNT(DISTINCT {id_expression})) "
                    "AS duplicate_id_rows",
                ]
            )
        if "confidence" in fields:
            confidence_expression, confidence_type, _ = fields["confidence"]
            if any(
                token in confidence_type.upper()
                for token in ("INT", "DECIMAL", "DOUBLE", "FLOAT", "HUGEINT")
            ):
                select_expressions.extend(
                    [
                        f"AVG({confidence_expression}) AS confidence_avg",
                        f"MIN({confidence_expression}) AS confidence_min",
                        f"QUANTILE_CONT({confidence_expression}, 0.5) "
                        "AS confidence_median",
                        f"MAX({confidence_expression}) AS confidence_max",
                        f"COUNTIF({confidence_expression} < 0.5) "
                        "AS confidence_lt_0_50",
                        f"COUNTIF({confidence_expression} >= 0.5 AND "
                        f"{confidence_expression} < 0.75) AS confidence_0_50_0_75",
                        f"COUNTIF({confidence_expression} >= 0.75 AND "
                        f"{confidence_expression} < 0.9) AS confidence_0_75_0_90",
                        f"COUNTIF({confidence_expression} >= 0.9 AND "
                        f"{confidence_expression} < 0.95) AS confidence_0_90_0_95",
                        f"COUNTIF({confidence_expression} >= 0.95) "
                        "AS confidence_ge_0_95",
                        f"COUNTIF({confidence_expression} IS NULL) "
                        "AS confidence_null",
                    ]
                )

        aggregate = connection.execute(
            "SELECT " + ", ".join(select_expressions) + " FROM source_data"
        )
        aggregate_row = aggregate.fetchone()
        aggregate_values = dict(
            zip((item[0] for item in aggregate.description), aggregate_row)
        )
        field_rows = []
        for name, (expression, data_type, definition) in fields.items():
            count = int(aggregate_values[metric_aliases[name]] or 0)
            field_rows.append(
                {
                    "field": name,
                    "source_path": FIELD_DISPLAY_PATHS.get(
                        name, expression.replace('"', "")
                    ),
                    "data_type": data_type,
                    "available_count": count,
                    "available_pct": _pct(count, row_count),
                    "definition": definition,
                }
            )
        _write_csv(
            output_dir / "field_availability.csv",
            [
                "field",
                "source_path",
                "data_type",
                "available_count",
                "available_pct",
                "definition",
            ],
            field_rows,
        )

        category_expression = fields.get("category_primary", (None, None, None))[0]
        category_rows = []
        if category_expression:
            category_rows = _category_profile(
                connection,
                category_expression,
                fields,
                row_count,
                output_dir / "category_profile.csv",
            )

        status_expression = fields.get("operating_status_value", (None, None, None))[0]
        if not status_expression:
            status_expression = fields.get("operating_status", (None, None, None))[0]
        status_rows: list[dict[str, Any]] = []
        if status_expression:
            raw_statuses = connection.execute(
                "SELECT CAST("
                + status_expression
                + " AS VARCHAR) AS status, COUNT(*) AS row_count "
                "FROM source_data GROUP BY 1 ORDER BY row_count DESC LIMIT 50"
            ).fetchall()
            status_rows = [
                {
                    "operating_status": value or "(null)",
                    "row_count": int(count),
                    "share_of_dataset_pct": _pct(int(count), row_count),
                }
                for value, count in raw_statuses
            ]
            _write_csv(
                output_dir / "operating_status.csv",
                ["operating_status", "row_count", "share_of_dataset_pct"],
                status_rows,
            )

        downloader_rows = type_manifest.get("row_count")
        if downloader_rows is not None and int(downloader_rows) != row_count:
            raise ValueError(
                "Số dòng DuckDB không khớp với manifest downloader: "
                f"{row_count} != {downloader_rows}."
            )

        profile_metrics = {
            "row_count": row_count,
            "column_count": len(schema_rows),
            "distinct_id_count": aggregate_values.get("distinct_ids"),
            "null_id_count": aggregate_values.get("null_ids"),
            "duplicate_id_rows": aggregate_values.get("duplicate_id_rows"),
            "confidence_avg": aggregate_values.get("confidence_avg"),
            "confidence_min": aggregate_values.get("confidence_min"),
            "confidence_median": aggregate_values.get("confidence_median"),
            "confidence_max": aggregate_values.get("confidence_max"),
            "confidence_distribution": [
                {
                    "range": label,
                    "row_count": int(aggregate_values.get(alias) or 0),
                    "share_of_dataset_pct": _pct(
                        int(aggregate_values.get(alias) or 0), row_count
                    ),
                }
                for label, alias in (
                    ("< 0.50", "confidence_lt_0_50"),
                    ("[0.50, 0.75)", "confidence_0_50_0_75"),
                    ("[0.75, 0.90)", "confidence_0_75_0_90"),
                    ("[0.90, 0.95)", "confidence_0_90_0_95"),
                    ("[0.95, 1.00]", "confidence_ge_0_95"),
                    ("NULL", "confidence_null"),
                )
                if alias in aggregate_values
            ],
            "field_availability": field_rows,
            "category_top_20": category_rows[:20],
            "operating_status": status_rows,
        }
    finally:
        connection.close()

    profile_metrics["geometry"] = _profile_geometry(files)
    _write_csv(
        output_dir / "confidence_distribution.csv",
        ["range", "row_count", "share_of_dataset_pct"],
        profile_metrics["confidence_distribution"],
    )
    (output_dir / "geometry_profile.json").write_text(
        json.dumps(profile_metrics["geometry"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    environment = {
        "python_version": platform.python_version(),
        "duckdb_version": _package_version("duckdb"),
        "pyarrow_version": _package_version("pyarrow"),
        "overturemaps_version": _package_version("overturemaps"),
        "shapely_version": _package_version("shapely"),
        "report_tool_path": Path(__file__).resolve().as_posix(),
        "report_tool_sha256": _sha256_file(Path(__file__).resolve()),
        "profile_tool_path": Path(profile_files.__code__.co_filename)
        .resolve()
        .as_posix(),
        "profile_tool_sha256": _sha256_file(
            Path(profile_files.__code__.co_filename).resolve()
        ),
        "requirements_sha256": _sha256_file(Path("requirements.txt")),
    }
    spike_manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": label,
        "input_files": [
            {
                "path": path.as_posix(),
                "bytes": path.stat().st_size,
            }
            for path in files
        ],
        "download_run_manifest_path": run_manifest_path.as_posix(),
        "download_run_manifest_sha256": _sha256_file(run_manifest_path),
        "type_manifest_path": type_manifest_path.as_posix(),
        "type_manifest_sha256": _sha256_file(type_manifest_path),
        "download_provenance": run_manifest,
        "type_provenance": type_manifest,
        "profile_manifest": profile_manifest,
        "profile_metrics": profile_metrics,
        "environment": environment,
        "commercial_redistribution_approved": type_manifest.get(
            "commercial_redistribution_approved", False
        ),
        "buyer_demand_validated": False,
    }
    (output_dir / "spike_manifest.json").write_text(
        json.dumps(spike_manifest, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    _write_report(output_dir / "REPORT.md", spike_manifest)
    return spike_manifest


def _write_report(path: Path, manifest: dict[str, Any]) -> None:
    provenance = manifest["download_provenance"]
    type_info = manifest["type_provenance"]
    metrics = manifest["profile_metrics"]
    boundary = provenance.get("boundary_manifest", {})
    fields = metrics["field_availability"]
    field_by_name = {item["field"]: item for item in fields}
    candidate_rows = int(type_info.get("candidate_rows") or 0)
    excluded_rows = int(type_info.get("excluded_by_boundary_policy") or 0)
    excluded_pct = _pct(excluded_rows, candidate_rows)
    size_estimate = provenance.get("size_estimate", {})
    if size_estimate.get("candidate_bytes") is None:
        stac_preflight = "- STAC preflight: không có ước tính trong manifest."
    else:
        stac_preflight = (
            f"- STAC preflight: {size_estimate.get('candidate_files', 'N/A')} "
            f"file ứng viên, {size_estimate['candidate_bytes']:,} byte."
        )
    field_rows = "\n".join(
        f"| `{item['source_path']}` | {item['available_count']:,} | "
        f"{item['available_pct']}% | {item['definition']} |"
        for item in fields
    )
    categories = metrics["category_top_20"]
    confidence_distribution = metrics["confidence_distribution"]
    confidence_rows = "\n".join(
        f"| {item['range']} | {item['row_count']:,} | "
        f"{item['share_of_dataset_pct']}% |"
        for item in confidence_distribution
    ) or "| (không có confidence số) | — | — |"
    geometry = metrics.get("geometry", {})
    if geometry.get("status") == "completed":
        geometry_summary = (
            f"- Shapely kiểm tra {geometry['row_count']:,} geometry: "
            f"hợp lệ {geometry['valid_count']:,} ({geometry['valid_pct_nonnull']}% "
            f"trên geometry không null), không hợp lệ {geometry['invalid_count']:,}, "
            f"WKB không giải mã được {geometry['unparseable_wkb_count']:,}, "
            f"geometry rỗng {geometry['empty_count']:,}, null "
            f"{geometry['null_count']:,}. Phân tích theo batch; xem "
            "`geometry_profile.json`."
        )
    else:
        geometry_summary = (
            "- Geometry validity chưa đo được: "
            f"{geometry.get('reason', geometry.get('status', 'không rõ'))}. "
            "DuckDB spatial extension không được cài tự động."
        )
    category_rows = "\n".join(
        f"| {item['category_primary']} | {item['row_count']:,} | "
        f"{item['share_of_dataset_pct']}% | "
        f"{item.get('websites_available_pct', '')} | "
        f"{item.get('phones_available_pct', '')} | "
        f"{item.get('addresses_available_pct', '')} |"
        for item in categories
    ) or "| (không có category chính trong schema) | — | — | — | — | — |"

    lines = [
        "# Báo cáo Mini Data Spike — Overture Places Hoa Kỳ",
        "",
        f"- Thời điểm tạo: `{manifest['generated_at_utc']}`",
        f"- Release Overture: `{provenance['resolved_release']}`",
        f"- Phạm vi: `{provenance['region']}`; theme `places`, type `place`.",
        f"- Số dòng sau lọc: **{metrics['row_count']:,}**.",
        f"- Số cột: **{metrics['column_count']}**.",
        f"- File đầu ra: **{type_info.get('output_bytes', 0):,} byte**; "
        f"SHA-256 `{type_info.get('sha256')}`.",
        "",
        "## Kết luận điều hành",
        "",
        "Báo cáo này là bằng chứng về quy mô/schema/độ sẵn có trường của nguồn "
        "dữ liệu sau lọc Hoa Kỳ. Nó **không** chứng minh mức sẵn sàng chi trả, "
        "khả năng bán trên marketplace hay quyền tái phân phối thương mại. "
        "Chưa kiểm chứng nhu cầu người mua; trạng thái giấy phép vẫn phải được "
        "rà soát theo từng nguồn thành phần.",
        "",
        "## Phạm vi và provenance",
        "",
        f"- Census: TIGERweb ACS2025 layer `{boundary.get('layer_id')}`, "
        f"{boundary.get('feature_count')} đơn vị; "
        f"SHA-256 `{boundary.get('sha256')}`.",
        f"- Overture source: `{type_info.get('source_data_url')}`; STAC catalog: "
        f"`{type_info.get('release_catalog_url')}`.",
        f"- Thời gian ingest UTC: bắt đầu `{provenance.get('started_at_utc')}`, "
        f"đọc nguồn `{type_info.get('accessed_at_utc')}`, hoàn tất "
        f"`{type_info.get('completed_at_utc')}`.",
        stac_preflight,
        f"- Số dòng ứng viên từ các bbox: {candidate_rows:,}; "
        f"được giữ sau phép `covered_by`: {type_info.get('us_rows', 0):,}; "
        f"bị loại theo chính sách biên: "
        f"{excluded_rows:,} ({excluded_pct}% candidate). Đây không phải số đếm "
        "thuần túy các feature ngoài Hoa Kỳ: predicate cũng loại geometry null/"
        "không giải mã được hoặc không được polygon bao phủ hoàn toàn.",
        f"- Trạng thái rà soát giấy phép: `{type_info.get('license_review_state')}`; "
        f"đã chấp thuận tái phân phối thương mại: "
        f"`{type_info.get('commercial_redistribution_approved')}`.",
        f"- Config SHA-256: `{provenance.get('config_sha256')}`.",
        f"- Downloader SHA-256: "
        f"`{provenance.get('tool_provenance', {}).get('sha256')}`.",
        "",
        "## Độ sẵn có trường",
        "",
        "Mẫu số là toàn bộ dòng đầu ra. Với list chuỗi, trường được coi là có "
        "dữ liệu khi còn ít nhất một phần tử không null/không trắng; list struct "
        "được đếm riêng và các trường con có chỉ số riêng. Chuỗi scalar phải "
        "không trắng sau `TRIM`; các kiểu khác phải không null. "
        "`profile/column_profile.csv` tách NULL, chuỗi scalar trắng và list rỗng "
        "ở cấp cột; `field_availability.csv` đo thêm giá trị hữu dụng trong list.",
        "",
        "| Trường | Dòng có dữ liệu | Tỷ lệ | Định nghĩa |",
        "|---|---:|---:|---|",
        field_rows or "| (không tìm thấy trường sản phẩm trong schema) | — | — | — |",
        "",
        "## Nhóm phân loại và trường sản phẩm",
        "",
        "Bảng dưới là tối đa 20 category chính theo số dòng. CSV đầy đủ (tối đa "
        "100 nhóm) ở `category_profile.csv`.",
        "",
        "| Category chính | Số dòng | Tỷ trọng | Website có dữ liệu | Phone có dữ liệu | Address có dữ liệu |",
        "|---|---:|---:|---:|---:|---:|",
        category_rows,
        "",
        "## Geometry",
        "",
        geometry_summary,
        "",
        "## Chỉ số định danh và confidence",
        "",
        f"- ID phân biệt: `{metrics.get('distinct_id_count')}`; ID null: "
        f"`{metrics.get('null_id_count')}`; dòng ID trùng vượt mức đầu tiên: "
        f"`{metrics.get('duplicate_id_rows')}`.",
        f"- Confidence (nếu là trường số): trung bình "
        f"`{metrics.get('confidence_avg')}`, median "
        f"`{metrics.get('confidence_median')}`, min `{metrics.get('confidence_min')}`, "
        f"max `{metrics.get('confidence_max')}`.",
        "- Phân bố confidence theo khoảng:",
        "",
        "| Khoảng confidence | Số dòng | Tỷ trọng |",
        "|---|---:|---:|",
        confidence_rows,
        "",
        "- Phân bố trạng thái hoạt động (`operating_status`, nếu có) nằm trong "
        "`operating_status.csv`. Giá trị null/thiếu không được diễn giải là địa "
        "điểm đã đóng cửa.",
        "",
        "",
        "## Ý nghĩa cho nghiên cứu sản phẩm",
        "",
        f"- Category chính có ở {field_by_name.get('category_primary', {}).get('available_pct', 'N/A')}% "
        f"dòng; website {field_by_name.get('websites', {}).get('available_pct', 'N/A')}%, "
        f"phone {field_by_name.get('phones', {}).get('available_pct', 'N/A')}% và "
        f"email {field_by_name.get('emails', {}).get('available_pct', 'N/A')}%. "
        "Vì vậy không nên hứa một tỷ lệ có dữ liệu đồng nhất cho mọi loại địa điểm.",
        f"- Các thành phần địa chỉ đo được gồm freeform "
        f"{field_by_name.get('address_freeform', {}).get('available_pct', 'N/A')}%, "
        f"locality {field_by_name.get('address_locality', {}).get('available_pct', 'N/A')}%, "
        f"postcode {field_by_name.get('address_postcode', {}).get('available_pct', 'N/A')}% "
        "và region "
        f"{field_by_name.get('address_region', {}).get('available_pct', 'N/A')}%.",
        f"- Operating status có giá trị ở "
        f"{field_by_name.get('operating_status', {}).get('available_pct', 'N/A')}% "
        "dòng; phần còn lại là thiếu trạng thái, không đồng nghĩa đã đóng cửa.",
        "- Dùng `field_availability.csv` và `category_profile.csv` để chọn category "
        "mà thông tin liên hệ/địa chỉ có độ phủ đủ cho một giả thuyết sản phẩm.",
        "- Đối chiếu trường nguồn với nhu cầu của người mua bằng phỏng vấn hoặc "
        "thử nghiệm chào bán trên marketplace; không tự đặt ngưỡng đạt sau khi "
        "đã nhìn thấy số.",
        "- Chỉ xây enrichment sau khi xác nhận có khoảng trống cụ thể và quyền dùng "
        "từng nguồn. Mọi tuyên bố “đầy đủ/chính xác/cập nhật” cần phép đo riêng.",
        "",
        "## Giới hạn",
        "",
        "- Bbox chỉ là tiền lọc; record ngoài Hoa Kỳ có thể được đọc tạm. Output "
        "chỉ giữ geometry được Census polygon bao phủ hoàn toàn; feature cắt biên "
        "bị loại thay vì clipping.",
        "- Tỷ lệ có trường không đánh giá tính đúng/sai, hợp lệ, mới hay liên hệ "
        "được. Một list có phần tử vẫn có thể chứa giá trị sai hoặc cũ.",
        "- Snapshot đo một release và một ranh giới Census 2025; không đại diện cho "
        "tốc độ cập nhật hoặc mọi thời điểm.",
        "- Chưa xác minh quyền thương mại/tái phân phối; không xuất bản hoặc bán "
        "snapshot này trước khi hoàn tất rà soát giấy phép/ghi công.",
        "- Dữ liệu chất lượng không thay thế bằng chứng marketplace, payout hoặc "
        "giao dịch trả phí.",
        "",
        "## Tệp đi kèm",
        "",
        "- `profile/column_profile.csv`: schema và null/blank/empty-list theo cột.",
        "- `field_availability.csv`: tỷ lệ có dữ liệu của các trường sản phẩm.",
        "- `category_profile.csv`: quy mô và tỷ lệ trường theo category chính.",
        "- `operating_status.csv`: phân bố trạng thái hoạt động nếu có.",
        "- `confidence_distribution.csv`: phân bố confidence theo khoảng.",
        "- `geometry_profile.json`: kiểm tra geometry theo batch.",
        "- `spike_manifest.json`: nguồn, hash, package và chỉ số đầy đủ.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tạo báo cáo DuckDB tổng hợp cho snapshot Overture Places Hoa Kỳ."
    )
    parser.add_argument("--input", required=True, help="Tệp hoặc thư mục GeoParquet cục bộ.")
    parser.add_argument("--output", required=True, type=Path, help="Thư mục báo cáo.")
    parser.add_argument("--label", required=True, help="Nhãn nguồn/release cho báo cáo.")
    parser.add_argument("--run-manifest", type=Path, help="Manifest của lần tải.")
    parser.add_argument("--type-manifest", type=Path, help="Manifest của feature type.")
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        manifest = generate_report(
            args.input,
            args.output,
            args.label,
            args.run_manifest,
            args.type_manifest,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    print(
        f"Đã tạo báo cáo cho {manifest['profile_metrics']['row_count']:,} dòng: "
        f"{(args.output / 'REPORT.md').resolve()}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
