#!/usr/bin/env python3
"""Tạo báo cáo HTML quyết định từ các artifact tổng hợp của Mini Data Spike."""

from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REPORT_DIR = Path("reports/overture_places_us_spike_2026-10-21.0")
FIELD_LABELS = {
    "category_primary": "Category chính",
    "websites": "Website",
    "phones": "Phone",
    "emails": "Email",
    "operating_status": "Trạng thái hoạt động",
    "address_freeform": "Địa chỉ hiển thị",
    "address_locality": "Thành phố / locality",
    "address_postcode": "ZIP / postcode",
    "address_region": "Bang / region",
    "address_country": "Quốc gia",
    "source_license": "License trong provenance",
}
FIELD_ORDER = tuple(FIELD_LABELS)
CANDIDATE_CATEGORIES = (
    "real_estate_agent",
    "contractor",
    "automotive_repair",
    "insurance_agency",
    "professional_service",
    "doctors_office",
)
LICENSE_COLORS = {
    "CDLA-Permissive-2.0": "#1b7465",
    "Apache-2.0": "#db633e",
    "CC0-1.0": "#547ba4",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _integer(value: Any) -> int:
    return int(value or 0)


def _number(value: Any) -> float:
    return float(value or 0)


def _fmt_int(value: Any) -> str:
    return f"{_integer(value):,}"


def _fmt_pct(value: Any) -> str:
    return f"{_number(value):.1f}%"


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _short_label(value: str, limit: int = 28) -> str:
    label = value.replace("_", " ")
    if len(label) <= limit:
        return label
    return label[: limit - 1] + "…"


def _mix(start: tuple[int, int, int], end: tuple[int, int, int], fraction: float) -> str:
    fraction = min(1.0, max(0.0, fraction))
    channels = tuple(round(a + (b - a) * fraction) for a, b in zip(start, end))
    return "#{:02x}{:02x}{:02x}".format(*channels)


def _heat_color(pct: float) -> str:
    return _mix((248, 229, 202), (168, 221, 193), pct / 100)


def _bar_chart(
    rows: list[tuple[str, float, str]],
    *,
    value_max: float,
    value_suffix: str = "%",
    width: int = 940,
    label_width: int = 245,
    bar_width: int = 540,
    row_height: int = 34,
    color: str = "#1b7465",
) -> str:
    height = max(90, len(rows) * row_height + 22)
    parts = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Biểu đồ thanh ngang">',
        '<line x1="0" y1="5" x2="0" y2="5" stroke="none"/>',
    ]
    for index, (label, value, display) in enumerate(rows):
        y = index * row_height + 8
        bar_len = max(2.0, bar_width * value / value_max) if value_max else 0
        parts.append(
            f'<g><title>{_escape(label)}: {_escape(display)}</title>'
            f'<text x="0" y="{y + 15}" class="chart-label">{_escape(_short_label(label))}</text>'
            f'<rect x="{label_width}" y="{y}" width="{bar_width}" height="19" rx="9.5" '
            'fill="#e8e5da"/>'
            f'<rect x="{label_width}" y="{y}" width="{bar_len:.1f}" height="19" rx="9.5" '
            f'fill="{color}"/>'
            f'<text x="{label_width + bar_width + 12}" y="{y + 15}" class="chart-value">'
            f'{_escape(display)}</text></g>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _column_chart(rows: list[tuple[str, float, str]]) -> str:
    width, height = 760, 260
    left, right, top, bottom = 42, 20, 16, 56
    plot_h = height - top - bottom
    plot_w = width - left - right
    max_value = max((value for _, value, _ in rows), default=1) or 1
    gap = 12
    col_w = (plot_w - gap * (len(rows) - 1)) / max(1, len(rows))
    parts = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Phân bố confidence theo khoảng">',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{width - right}" '
        f'y2="{top + plot_h}" stroke="#c9c8ba"/>',
    ]
    for index, (label, value, display) in enumerate(rows):
        x = left + index * (col_w + gap)
        bar_h = plot_h * value / max_value
        y = top + plot_h - bar_h
        color = "#d95e3b" if index == 0 else "#2c7e6b"
        parts.append(
            f'<g><title>{_escape(label)}: {_escape(display)}</title>'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{col_w:.1f}" height="{bar_h:.1f}" '
            f'rx="8" fill="{color}"/>'
            f'<text x="{x + col_w / 2:.1f}" y="{max(14, y - 7):.1f}" '
            'text-anchor="middle" class="chart-value">'
            f'{_escape(display)}</text>'
            f'<text x="{x + col_w / 2:.1f}" y="{height - 26}" text-anchor="middle" '
            f'class="chart-label">{_escape(label)}</text></g>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _stacked_bar(rows: list[dict[str, str]]) -> str:
    colors = {
        "open": "#1b7465",
        "permanently_closed": "#db633e",
        "temporarily_closed": "#d7a548",
        "(null)": "#c5c8bf",
    }
    labels = {
        "open": "Đang mở theo dữ liệu",
        "permanently_closed": "Đóng cửa vĩnh viễn",
        "temporarily_closed": "Đóng cửa tạm thời",
        "(null)": "Thiếu trạng thái",
    }
    x, y, width, height = 12, 20, 896, 28
    parts = [
        f'<svg class="chart-svg" viewBox="0 0 940 100" role="img" '
        'aria-label="Tỷ trọng operating status">',
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="14" fill="#e8e5da"/>',
    ]
    position = x
    total = sum(_integer(row["row_count"]) for row in rows) or 1
    legend = []
    for row in rows:
        key = row["operating_status"]
        count = _integer(row["row_count"])
        fraction = count / total
        segment = width * fraction
        parts.append(
            f'<g><title>{_escape(labels.get(key, key))}: '
            f'{_fmt_int(count)} ({_fmt_pct(row["share_of_dataset_pct"])})</title>'
            f'<rect x="{position:.2f}" y="{y}" width="{segment:.2f}" height="{height}" '
            f'fill="{colors.get(key, "#777")}" /></g>'
        )
        position += segment
        legend.append(
            f'<span class="legend-item"><i style="--swatch:{colors.get(key, "#777")}"></i>'
            f'{_escape(labels.get(key, key))} <b>{_fmt_pct(row["share_of_dataset_pct"])}</b>'
            f' <small>{_fmt_int(count)}</small></span>'
        )
    parts.append("</svg>")
    return "".join(parts) + '<div class="legend">' + "".join(legend) + "</div>"


def _heatmap_table(rows: list[dict[str, str]]) -> str:
    headers = ("Website", "Phone", "Email")
    fields = ("websites_available_pct", "phones_available_pct", "emails_available_pct")
    body = []
    for row in rows:
        cells = []
        for field in fields:
            value = _number(row[field])
            cells.append(
                f'<td style="background:{_heat_color(value)}">{value:.1f}%</td>'
            )
        body.append(
            f'<tr><th scope="row">{_escape(_short_label(row["category_primary"], 32))}</th>'
            f'<td class="numeric">{_fmt_int(row["row_count"])}</td>'
            f'{"".join(cells)}</tr>'
        )
    return (
        '<div class="table-scroll"><table class="heat-table">'
        '<thead><tr><th scope="col">Category chính</th><th scope="col">Số dòng</th>'
        + "".join(f'<th scope="col">{header}</th>' for header in headers)
        + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
    )


def _license_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"source_items": 0, "scope_groups": 0, "providers": set()}
    )
    for row in rows:
        item = grouped[row["license"]]
        item["source_items"] += _integer(row["source_item_count"])
        item["scope_groups"] += 1
        item["providers"].add(row["provider"])
    result = []
    for license_name, item in grouped.items():
        result.append(
            {
                "license": license_name,
                "source_items": item["source_items"],
                "scope_groups": item["scope_groups"],
                "providers": sorted(item["providers"]),
            }
        )
    return sorted(result, key=lambda row: row["source_items"], reverse=True)


def _candidate_table(
    categories: list[dict[str, str]], *, limit: int | None = None
) -> str:
    by_name = {row["category_primary"]: row for row in categories}
    body = []
    names = CANDIDATE_CATEGORIES[:limit] if limit else CANDIDATE_CATEGORIES
    for name in names:
        row = by_name.get(name)
        if not row:
            continue
        body.append(
            "<tr>"
            f'<th scope="row">{_escape(name.replace("_", " "))}</th>'
            f'<td class="numeric">{_fmt_int(row["row_count"])}</td>'
            f'<td>{_fmt_pct(row["share_of_dataset_pct"])}</td>'
            f'<td>{_fmt_pct(row["websites_available_pct"])}</td>'
            f'<td>{_fmt_pct(row["phones_available_pct"])}</td>'
            f'<td>{_fmt_pct(row["emails_available_pct"])}</td>'
            "</tr>"
        )
    return (
        '<div class="table-scroll"><table>'
        "<thead><tr><th>Category ứng viên</th><th>Số dòng</th><th>Tỷ trọng</th>"
        "<th>Website</th><th>Phone</th><th>Email</th></tr></thead>"
        "<tbody>" + "".join(body) + "</tbody></table></div>"
    )


def _license_table(rows: list[dict[str, Any]]) -> str:
    body = []
    for row in rows:
        body.append(
            "<tr>"
            f'<th scope="row"><span class="license-mark" '
            f'style="--swatch:{LICENSE_COLORS.get(row["license"], "#777")}"></span>'
            f'{_escape(row["license"])}</th>'
            f'<td class="numeric">{row["scope_groups"]}</td>'
            f'<td class="numeric">{_fmt_int(row["source_items"])}</td>'
            f'<td>{_escape(", ".join(row["providers"]))}</td>'
            "</tr>"
        )
    return (
        '<div class="table-scroll"><table>'
        "<thead><tr><th>License quan sát được</th><th>Nhóm scope</th>"
        "<th>Source-item entries*</th><th>Provider</th></tr></thead>"
        "<tbody>" + "".join(body) + "</tbody></table></div>"
    )


def _render_html(report_dir: Path) -> str:
    fields = _read_csv(report_dir / "field_availability.csv")
    categories = _read_csv(report_dir / "category_profile.csv")
    confidence = _read_csv(report_dir / "confidence_distribution.csv")
    statuses = _read_csv(report_dir / "operating_status.csv")
    licenses = _read_csv(report_dir / "license_inventory.csv")
    geometry = _read_json(report_dir / "geometry_profile.json")
    manifest = _read_json(report_dir / "spike_manifest.json")

    metrics = manifest["profile_metrics"]
    run = manifest["download_provenance"]
    dataset = run["datasets"][0]
    file_entry = manifest["input_files"][0]
    row_count = _integer(metrics["row_count"])
    candidate_count = _integer(dataset["candidate_rows"])
    retained_count = _integer(dataset["us_rows"])
    excluded_count = _integer(dataset["excluded_by_boundary_policy"])
    excluded_pct = 100 * excluded_count / candidate_count if candidate_count else 0
    available = {row["field"]: row for row in fields}

    field_keys = [key for key in FIELD_ORDER if key in available]
    field_chart_rows = [
        (
            FIELD_LABELS[key],
            _number(available[key]["available_pct"]),
            _fmt_pct(available[key]["available_pct"]),
        )
        for key in field_keys
    ]
    top_categories = sorted(
        categories, key=lambda row: _integer(row["row_count"]), reverse=True
    )[:12]
    category_chart_rows = [
        (
            "(không có category)" if row["category_primary"].startswith("(")
            else row["category_primary"],
            _integer(row["row_count"]),
            _fmt_int(row["row_count"]),
        )
        for row in top_categories
    ]
    confidence_rows = [
        (
            row["range"],
            _number(row["share_of_dataset_pct"]),
            _fmt_pct(row["share_of_dataset_pct"]),
        )
        for row in confidence
        if row["range"] != "NULL"
    ]
    license_summary = _license_rows(licenses)
    license_chart_rows = [
        (
            row["license"],
            row["source_items"],
            _fmt_int(row["source_items"]),
        )
        for row in license_summary
    ]
    license_max = max((row[1] for row in license_chart_rows), default=1)
    license_chart = _bar_chart(
        license_chart_rows,
        value_max=license_max,
        value_suffix="",
        label_width=270,
        bar_width=500,
        row_height=40,
        color="#547ba4",
    )
    status_pct = {
        row["operating_status"]: row["share_of_dataset_pct"] for row in statuses
    }
    category_missing = 100 - _number(available["category_primary"]["available_pct"])
    total_bytes = _integer(file_entry["bytes"])
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    checksum = dataset.get("sha256", "Không có trong manifest")
    top_candidate_names = [
        row["category_primary"] for row in top_categories
    ]
    top_candidate_heat = [
        row
        for row in categories
        if row["category_primary"] in top_candidate_names
    ]
    top_candidate_heat.sort(
        key=lambda row: _integer(row["row_count"]), reverse=True
    )

    license_bar_rows = []
    for row in license_chart_rows:
        license_name = row[0]
        color = LICENSE_COLORS.get(license_name, "#547ba4")
        license_bar_rows.append((row[0], row[1], row[2]))
    license_chart = _bar_chart(
        license_bar_rows,
        value_max=license_max,
        label_width=270,
        bar_width=500,
        row_height=40,
        color="#547ba4",
    )

    kpis = [
        ("18.56M", "địa điểm sau lọc", "row count"),
        (_fmt_pct(available["websites"]["available_pct"]), "có website", "có ít nhất một giá trị"),
        (_fmt_pct(available["phones"]["available_pct"]), "có phone", "có ít nhất một giá trị"),
        (_fmt_pct(available["category_primary"]["available_pct"]), "có category chính", f"{category_missing:.1f}% thiếu"),
    ]
    kpi_html = "".join(
        f'<article class="kpi"><div class="kpi-value">{_escape(value)}</div>'
        f'<div class="kpi-label">{_escape(label)}</div>'
        f'<div class="kpi-note">{_escape(note)}</div></article>'
        for value, label, note in kpis
    )
    candidate_rows = _candidate_table(categories)
    top_table_rows = []
    for row in top_categories:
        category = row["category_primary"]
        top_table_rows.append(
            "<tr>"
            f'<th scope="row">{_escape("(không có category chính)" if category.startswith("(") else category.replace("_", " "))}</th>'
            f'<td class="numeric">{_fmt_int(row["row_count"])}</td>'
            f'<td>{_fmt_pct(row["share_of_dataset_pct"])}</td>'
            f'<td>{_fmt_pct(row["websites_available_pct"])}</td>'
            f'<td>{_fmt_pct(row["phones_available_pct"])}</td>'
            f'<td>{_fmt_pct(row["emails_available_pct"])}</td>'
            "</tr>"
        )
    top_table = (
        '<div class="table-scroll"><table><thead><tr><th>Category</th><th>Số dòng</th>'
        "<th>Tỷ trọng</th><th>Website</th><th>Phone</th><th>Email</th></tr></thead>"
        "<tbody>" + "".join(top_table_rows) + "</tbody></table></div>"
    )

    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Báo cáo trực quan hỗ trợ quyết định từ Mini Data Spike Overture Places Hoa Kỳ.">
  <title>Places / Báo cáo quyết định — DATA-2026</title>
  <style>
    :root {{
      color-scheme: light;
      --paper: #f2f0e6;
      --card: #fffdf7;
      --ink: #1d302d;
      --muted: #66746d;
      --line: #d8d9cc;
      --forest: #1b7465;
      --deep: #173f39;
      --lime: #d8e970;
      --coral: #db633e;
      --blue: #547ba4;
      --sand: #e9e3d5;
      --shadow: 0 18px 50px rgba(32, 48, 43, .08);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(ellipse at 88% 4%, rgba(216,233,112,.30), transparent 22rem),
        linear-gradient(135deg, rgba(27,116,101,.035) 25%, transparent 25%) 0 0/28px 28px,
        var(--paper);
      font-family: "Trebuchet MS", "Segoe UI", sans-serif;
      line-height: 1.55;
    }}
    a {{ color: var(--forest); text-underline-offset: 3px; }}
    .shell {{ max-width: 1320px; margin: 0 auto; padding: 0 30px 72px; }}
    .masthead {{
      display: flex; justify-content: space-between; align-items: center;
      padding: 22px 0; border-bottom: 1px solid var(--line);
      color: var(--muted); font: 700 11px/1.2 Consolas, monospace;
      letter-spacing: .13em; text-transform: uppercase;
    }}
    .masthead span:last-child {{ text-align: right; }}
    .hero {{
      display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(250px, .55fr);
      gap: 36px; align-items: end; padding: 64px 0 46px;
      animation: rise .7s ease-out both;
    }}
    .eyebrow {{ color: var(--coral); font: 700 12px Consolas, monospace; letter-spacing: .16em; text-transform: uppercase; }}
    h1 {{
      max-width: 850px; margin: 16px 0 14px;
      font: 500 clamp(42px, 7vw, 82px)/.98 Georgia, "Times New Roman", serif;
      letter-spacing: -.055em;
    }}
    .hero p {{ max-width: 720px; margin: 0; color: var(--muted); font-size: 18px; }}
    .hero-stamp {{
      position: relative; padding: 25px; border: 1px solid var(--deep);
      background: var(--lime); box-shadow: 9px 9px 0 var(--deep); transform: rotate(1deg);
    }}
    .hero-stamp small {{ display: block; font: 700 11px Consolas, monospace; letter-spacing: .12em; text-transform: uppercase; }}
    .hero-stamp strong {{ display: block; margin: 8px 0 0; font: 500 38px/1 Georgia, serif; }}
    .hero-stamp span {{ display: block; margin-top: 8px; font-size: 13px; }}
    .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }}
    .kpi {{
      min-height: 142px; padding: 22px; background: var(--card);
      border: 1px solid var(--line); box-shadow: var(--shadow);
      animation: rise .55s ease-out both;
    }}
    .kpi:nth-child(2) {{ animation-delay: .08s; }}
    .kpi:nth-child(3) {{ animation-delay: .16s; }}
    .kpi:nth-child(4) {{ animation-delay: .24s; }}
    .kpi-value {{ font: 600 clamp(28px, 4vw, 42px)/1 Georgia, serif; color: var(--forest); }}
    .kpi-label {{ margin-top: 12px; font-weight: 700; }}
    .kpi-note {{ margin-top: 4px; color: var(--muted); font-size: 12px; }}
    .verdict {{
      display: grid; grid-template-columns: 1.2fr .8fr; gap: 22px;
      margin: 28px 0 48px; padding: 30px; color: #f5f2e7;
      background: var(--deep); border-radius: 2px;
    }}
    .verdict h2 {{ margin: 0 0 10px; font: 500 30px/1.1 Georgia, serif; }}
    .verdict p {{ margin: 0; color: #d6e2d9; }}
    .verdict-mark {{ padding: 18px 20px; border-left: 4px solid var(--lime); background: rgba(255,255,255,.06); }}
    .verdict-mark strong {{ display: block; color: var(--lime); font: 700 13px Consolas, monospace; letter-spacing: .08em; text-transform: uppercase; }}
    .verdict-mark span {{ display: block; margin-top: 8px; font-size: 15px; }}
    .section-head {{ display: flex; align-items: end; justify-content: space-between; gap: 20px; margin: 54px 0 18px; }}
    .section-kicker {{ color: var(--coral); font: 700 11px Consolas, monospace; letter-spacing: .14em; text-transform: uppercase; }}
    h2 {{ margin: 5px 0 0; font: 500 clamp(29px, 4vw, 42px)/1.05 Georgia, serif; letter-spacing: -.035em; }}
    .section-note {{ max-width: 460px; color: var(--muted); font-size: 13px; }}
    .grid-2 {{ display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 18px; }}
    .panel {{ min-width: 0; padding: 24px; background: var(--card); border: 1px solid var(--line); box-shadow: var(--shadow); }}
    .panel h3 {{ margin: 0 0 6px; font: 600 20px Georgia, serif; }}
    .panel p {{ margin: 4px 0 16px; color: var(--muted); font-size: 13px; }}
    .chart-svg {{ display: block; width: 100%; height: auto; overflow: visible; }}
    .chart-label {{ fill: #45554f; font: 12px "Trebuchet MS", sans-serif; }}
    .chart-value {{ fill: #1d302d; font: 700 11px Consolas, monospace; }}
    .legend {{ display: flex; flex-wrap: wrap; gap: 11px 18px; margin-top: 14px; }}
    .legend-item {{ display: inline-flex; align-items: center; gap: 7px; color: var(--muted); font-size: 12px; }}
    .legend-item i, .license-mark {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: var(--swatch); }}
    .legend-item b {{ color: var(--ink); }}
    .legend-item small {{ color: var(--muted); }}
    .table-scroll {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ padding: 11px 12px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: middle; }}
    thead th {{ color: var(--muted); font: 700 10px Consolas, monospace; letter-spacing: .08em; text-transform: uppercase; }}
    tbody th {{ font-weight: 700; }}
    td.numeric {{ font: 700 12px Consolas, monospace; white-space: nowrap; }}
    .heat-table td:not(.numeric) {{ text-align: center; font: 700 12px Consolas, monospace; min-width: 76px; }}
    .heat-table th:first-child {{ min-width: 190px; }}
    .heat-table td.numeric {{ min-width: 105px; }}
    .license-mark {{ margin-right: 8px; vertical-align: -1px; }}
    .callout {{
      margin: 18px 0 0; padding: 17px 20px; border-left: 4px solid var(--coral);
      background: #f9e9dc; color: #553e34; font-size: 13px;
    }}
    .callout.green {{ border-left-color: var(--forest); background: #e5f0e7; color: #294d43; }}
    .evidence-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }}
    .evidence-card {{ padding: 22px; background: var(--card); border-top: 4px solid var(--forest); }}
    .evidence-card.unknown {{ border-top-color: var(--coral); }}
    .evidence-card.stop {{ border-top-color: #d4ae42; }}
    .evidence-card h3 {{ margin: 0 0 8px; font: 600 20px Georgia, serif; }}
    .evidence-card p, .evidence-card li {{ color: var(--muted); font-size: 13px; }}
    .evidence-card ul {{ margin: 10px 0 0; padding-left: 18px; }}
    .steps {{ counter-reset: step; display: grid; grid-template-columns: repeat(3,1fr); gap: 14px; }}
    .step {{ position: relative; padding: 22px 22px 22px 58px; background: var(--deep); color: #f5f2e7; }}
    .step::before {{ counter-increment: step; content: "0" counter(step); position: absolute; left: 18px; top: 22px; color: var(--lime); font: 700 13px Consolas, monospace; }}
    .step strong {{ display: block; margin-bottom: 7px; }}
    .step span {{ color: #d1ddd6; font-size: 13px; }}
    .meta-table td:first-child {{ width: 180px; color: var(--muted); }}
    .mono {{ font-family: Consolas, monospace; overflow-wrap: anywhere; }}
    .footer {{ display: flex; justify-content: space-between; gap: 20px; margin-top: 58px; padding-top: 20px; border-top: 1px solid var(--line); color: var(--muted); font: 11px Consolas, monospace; }}
    @keyframes rise {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    @media (max-width: 850px) {{
      .hero {{ grid-template-columns: 1fr; }}
      .hero-stamp {{ max-width: 360px; }}
      .kpis {{ grid-template-columns: repeat(2, 1fr); }}
      .grid-2, .verdict {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 620px) {{
      .shell {{ padding: 0 16px 48px; }}
      .masthead {{ font-size: 9px; }}
      .hero {{ padding: 42px 0 32px; }}
      .hero p {{ font-size: 15px; }}
      .kpi {{ min-height: 120px; padding: 16px; }}
      .verdict {{ padding: 22px; }}
      .panel {{ padding: 18px 14px; }}
      .section-head {{ display: block; }}
      .section-note {{ margin-top: 10px; }}
      .evidence-grid, .steps {{ grid-template-columns: 1fr; }}
      .footer {{ display: block; }}
    }}
    @media print {{
      body {{ background: #fff; }}
      .shell {{ max-width: none; padding: 0; }}
      .kpi, .panel {{ box-shadow: none; break-inside: avoid; }}
      .verdict, .step {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
      .section-head {{ break-after: avoid; }}
      a {{ color: inherit; }}
    }}
  </style>
</head>
<body>
<main class="shell">
  <div class="masthead"><span>DATA-2026 / Decision brief 01</span><span>OVERTURE PLACES · US · OFFLINE REPORT</span></div>
  <header class="hero">
    <div>
      <div class="eyebrow">Nguồn cung đã đo · nhu cầu chưa xác minh</div>
      <h1>Places có dữ liệu.<br>Còn giá trị bán?</h1>
      <p>Bản tóm tắt trực quan để chọn giả thuyết nghiên cứu tiếp theo — không biến độ phủ dữ liệu thành kết luận về khách hàng.</p>
    </div>
    <div class="hero-stamp"><small>Release đã ghim</small><strong>{_escape(dataset["resolved_release"])}</strong><span>places / place · Hoa Kỳ theo boundary Census 2025</span></div>
  </header>

  <section class="kpis" aria-label="Chỉ số chính">
    {kpi_html}
  </section>

  <section class="verdict">
    <div><h2>Kết luận điều hành</h2><p>Snapshot đủ lớn và có độ phủ phone/website cao ở một số category, nhưng độ phủ khác nhau đáng kể theo ngành. Đây là tín hiệu để chọn câu hỏi nghiên cứu, chưa phải bằng chứng buyer demand, độ chính xác hay quyền bán lại.</p></div>
    <div class="verdict-mark"><strong>Quyết định hiện tại</strong><span>Không build/listing dataset thật. Tiếp tục pain-point discovery bằng dữ liệu tổng hợp và mockup không chứa record nguồn.</span></div>
  </section>

  <div class="section-head"><div><div class="section-kicker">01 / Field coverage</div><h2>Trường nào đủ dùng để thử giả thuyết?</h2></div><div class="section-note">Mẫu số là 18,560,038 feature. List chỉ tính có ít nhất một phần tử hữu dụng; đây không phải phép đo tính đúng, mới hay liên hệ được.</div></div>
  <div class="grid-2">
    <article class="panel"><h3>Độ sẵn có theo trường</h3><p>Địa chỉ và taxonomy tương đối đầy; email là trường yếu nhất trong nhóm liên hệ.</p>{_bar_chart(field_chart_rows, value_max=100, label_width=220, bar_width=500, row_height=32)}</article>
    <article class="panel"><h3>Độ phủ không đồng đều</h3><p>Chênh lệch theo category quyết định loại lời hứa nào có thể thử — không nên hứa một mức coverage chung.</p>
      <div class="evidence-card"><h3>Liên hệ toàn tập</h3><p><b>{_fmt_pct(available["websites"]["available_pct"])}</b> có website · <b>{_fmt_pct(available["phones"]["available_pct"])}</b> có phone · <b>{_fmt_pct(available["emails"]["available_pct"])}</b> có email.</p></div>
      <div class="callout">Địa chỉ ở cấp list có 100% feature có ít nhất một phần tử; từng child field vẫn thiếu: postcode {_fmt_pct(available["address_postcode"]["available_pct"])}, locality {_fmt_pct(available["address_locality"]["available_pct"])}, region {_fmt_pct(available["address_region"]["available_pct"])}.</div>
    </article>
  </div>

  <div class="section-head"><div><div class="section-kicker">02 / Category screen</div><h2>Quy mô lớn không đồng nghĩa niche tốt</h2></div><div class="section-note">Category là taxonomy nguồn, không phải phân khúc buyer đã được kiểm chứng. Các nhóm chỉ dùng để sàng lọc ban đầu.</div></div>
  <div class="grid-2">
    <article class="panel"><h3>12 nhóm có nhiều dòng nhất</h3><p>Cả nhóm thiếu category chính cũng được giữ để không che mất phần chưa phân loại.</p>{_bar_chart(category_chart_rows, value_max=max(row[1] for row in category_chart_rows), value_suffix="", label_width=250, bar_width=500, row_height=31, color="#db633e")}</article>
    <article class="panel"><h3>Ứng viên để kiểm chứng — chưa xếp hạng</h3><p>Chọn theo khả năng phân tích dữ liệu (volume + contact fields) בלבד; pain point, cạnh tranh, quyền enrichment và willingness-to-pay còn chưa biết.</p>{candidate_rows}<div class="callout">Không chọn niche chỉ từ bảng này. Cần nguồn pain point lặp lại, ít nhất một tín hiệu trả tiền và xác nhận quyền nguồn.</div></article>
  </div>

  <article class="panel" style="margin-top:18px"><h3>Heatmap liên hệ theo 12 category đầu</h3><p>Màu xanh hơn = tỷ lệ có ít nhất một giá trị cao hơn. Giá trị vẫn cần được kiểm tra chất lượng ngoài thực địa.</p>{_heatmap_table(top_candidate_heat)}</article>

  <div class="section-head"><div><div class="section-kicker">03 / Reliability signals</div><h2>Trạng thái và confidence cần đọc đúng nghĩa</h2></div><div class="section-note">Confidence là điểm do nguồn cung cấp; không diễn giải như xác suất đúng đã được hiệu chuẩn.</div></div>
  <div class="grid-2">
    <article class="panel"><h3>Operating status</h3><p>Thiếu status là missing, không phải “đã đóng cửa”.</p>{_stacked_bar(statuses)}
      <div class="callout">Open: {_fmt_pct(status_pct.get("open", 0))} · permanently closed: {_fmt_pct(status_pct.get("permanently_closed", 0))} · thiếu: {_fmt_pct(status_pct.get("(null)", 0))}. Không dùng giá trị thiếu để suy diễn closure.</div>
    </article>
    <article class="panel"><h3>Confidence bins</h3><p>Median {_number(metrics["confidence_median"]):.3f} · mean {_number(metrics["confidence_avg"]):.3f}. Không có đối chiếu ground truth trong spike.</p>{_column_chart(confidence_rows)}</article>
  </div>
  <div class="callout green">Geometry: {_fmt_int(geometry["valid_count"])} hợp lệ, {_fmt_int(geometry["invalid_count"])} không hợp lệ, {_fmt_int(geometry["null_count"])} null và {_fmt_int(geometry["empty_count"])} rỗng. Geometry hợp lệ không chứng minh pin chính xác ngoài thực tế.</div>

  <div class="section-head"><div><div class="section-kicker">04 / Rights & provenance</div><h2>License hỗn hợp — phân phối đang khóa</h2></div><div class="section-note">Đếm source-item scopes, không phải số doanh nghiệp duy nhất. Một feature có thể xuất hiện trong nhiều scope/license.</div></div>
  <div class="grid-2">
    <article class="panel"><h3>Source-item entries theo license</h3><p>Giữ nguyên field-level provenance trong `sources[*].property`.</p>{license_chart}<div class="callout">Inventory có {len(licenses)} tổ hợp provider/dataset/license/property; code quan sát: {", ".join(_escape(item["license"]) for item in license_summary)}. Không thấy ODbL trong snapshot Places này; join OSM vẫn cần rà riêng.</div></article>
    <article class="panel"><h3>Điều kiện phát hành hiện tại</h3><div class="table-scroll"><table class="meta-table"><tbody>
      <tr><td>CDLA-Permissive-2.0</td><td>Dùng/sửa/chia sẻ; khi chia sẻ Data, kèm toàn văn license.</td></tr>
      <tr><td>Apache-2.0</td><td>Kèm license, NOTICE áp dụng, giữ notices và đánh dấu sửa đổi.</td></tr>
      <tr><td>CC0-1.0</td><td>Cho phép rộng; quyền riêng tư, nhãn hiệu và luật khác vẫn áp dụng.</td></tr>
      <tr><td>Trạng thái repo</td><td><b>commercial_redistribution_approved = false</b></td></tr>
    </tbody></table></div><div class="callout">Đây là ghi nhận điều khoản chung, không phải phê duyệt cho một gói sản phẩm cụ thể. Xem <a href="../../docs/OVERTURE_LICENSE_POLICY.md">chính sách license Overture</a>.</div></article>
  </div>
  {_license_table(license_summary)}

  <div class="section-head"><div><div class="section-kicker">05 / Decision board</div><h2>Bằng chứng, giả định và điểm dừng</h2></div><div class="section-note">Dùng phần này để quyết định hành động tiếp theo, không dùng làm sales claim.</div></div>
  <div class="evidence-grid">
    <article class="evidence-card"><h3>Đã đo</h3><ul><li>{_fmt_int(row_count)} feature sau lọc.</li><li>{_fmt_int(metrics["distinct_id_count"])} ID phân biệt; null/trùng bằng 0.</li><li>Phone, website, taxonomy và geometry đã được đo.</li></ul></article>
    <article class="evidence-card unknown"><h3>Chưa biết</h3><ul><li>Buyer nào có vấn đề đủ cấp thiết.</li><li>Ai trả tiền, mức giá và định dạng cần mua.</li><li>Freshness, accuracy, deliverability và retention.</li></ul></article>
    <article class="evidence-card stop"><h3>Điểm dừng</h3><ul><li>Không xuất bản record nguồn khi rights/NOTICE chưa map cho sản phẩm.</li><li>Không build nếu chưa có pain point và tín hiệu thanh toán.</li><li>Không dùng dữ liệu cá nhân hoặc nguồn enrichment chưa duyệt.</li></ul></article>
  </div>

  <div class="section-head"><div><div class="section-kicker">06 / Next work</div><h2>Task kế tiếp: tìm vấn đề trả tiền thật</h2></div><div class="section-note">Theo roadmap hiện tại, ROAD-13 là pain-point scan trước Gate 2; chưa chuyển sang xây pipeline niche.</div></div>
  <div class="steps">
    <div class="step"><strong>Thu tín hiệu</strong><span>Ghi 20–25 pain point ở review, cộng đồng ngành và job freelance; mỗi dòng có buyer, công việc hiện tại, URL và ngày.</span></div>
    <div class="step"><strong>Thu hẹp có tiêu chí</strong><span>Gom 8–10 nhóm, rồi chọn Top 3 chỉ khi pain lặp lại, fit dữ liệu và không vướng rights/marketplace.</span></div>
    <div class="step"><strong>Kiểm chứng trả tiền</strong><span>Phỏng vấn buyer hoặc thử offer/mockup không chứa record nguồn. Ghi rõ “chưa có bằng chứng” nếu chưa thấy giao dịch.</span></div>
  </div>
  <div class="callout">Ứng viên chỉ để định hướng tìm kiếm ban đầu: `real_estate_agent`, `contractor`, `automotive_repair`, `insurance_agency`, `professional_service`, `doctors_office`. Đây không phải lựa chọn niche hoặc bằng chứng nhu cầu.</div>

  <div class="section-head"><div><div class="section-kicker">07 / Provenance</div><h2>Snapshot và phương pháp</h2></div><div class="section-note">Báo cáo này được dựng từ CSV/JSON tổng hợp trong repo; không đọc hoặc nhúng business record thô.</div></div>
  <article class="panel"><div class="table-scroll"><table class="meta-table"><tbody>
    <tr><td>Release / theme / type</td><td><span class="mono">{_escape(dataset["resolved_release"])} / places / place</span></td></tr>
    <tr><td>Phạm vi</td><td>{_escape(run["region_coverage"])}; lọc geometry được Census polygon bao phủ hoàn toàn.</td></tr>
    <tr><td>Candidate / retained</td><td>{_fmt_int(candidate_count)} / {_fmt_int(retained_count)}; loại { _fmt_int(excluded_count) } ({excluded_pct:.3f}%) theo predicate, không phải số thuần túy bản ghi ngoài Mỹ.</td></tr>
    <tr><td>Snapshot</td><td>{_fmt_int(total_bytes)} byte · SHA-256 <span class="mono">{_escape(checksum)}</span></td></tr>
    <tr><td>Census boundary</td><td>TIGERweb ACS2025 layer 80; {_fmt_int(run["boundary_manifest"]["feature_count"])} đơn vị; SHA-256 <span class="mono">{_escape(run["boundary_manifest"]["sha256"])}</span></td></tr>
    <tr><td>Ngày dựng report</td><td>{_escape(generated_at)}</td></tr>
    <tr><td>Artifact nguồn</td><td><span class="mono">REPORT.md · field_availability.csv · category_profile.csv · confidence_distribution.csv · operating_status.csv · geometry_profile.json · license_inventory.csv</span></td></tr>
  </tbody></table></div>
  <div class="callout">Báo cáo dùng address-region string thô để lấy coverage, không tạo bản đồ bang: có 155 giá trị region phân biệt nên cần chuẩn hóa/đối chiếu trước khi ra quyết định theo bang.</div></article>

  <footer class="footer"><span>DATA-2026 · Mini Data Spike / decision support</span><span>Generated { _escape(generated_at) } · print-to-PDF available</span></footer>
</main>
</body>
</html>
"""


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Tạo báo cáo HTML quyết định từ artifact Mini Data Spike."
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help="Thư mục chứa CSV/JSON tổng hợp của Mini Spike.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Đường dẫn HTML đầu ra (mặc định DECISION_REPORT.html trong report-dir).",
    )
    args = parser.parse_args()
    report_dir = args.report_dir.resolve()
    output = (args.output or report_dir / "DECISION_REPORT.html").resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    page = _render_html(report_dir)
    output.write_text(page, encoding="utf-8")
    print(f"Đã tạo báo cáo: {output}")
    print(f"Kích thước: {output.stat().st_size:,} byte")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
