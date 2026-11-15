#!/usr/bin/env python3
"""Tải các theme Overture đã chọn và chỉ giữ feature thuộc ranh giới Hoa Kỳ."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import shutil
import sys
import warnings
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from importlib import import_module
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.request import Request, urlopen
from urllib.parse import urlencode


STAC_CATALOG_URL = "https://stac.overturemaps.org/catalog.json"
OVERTURE_PY_DOCS_URL = "https://docs.overturemaps.org/getting-data/overturemaps-py/"
CENSUS_BOUNDARY_DOCS_URL = (
    "https://catalog.data.gov/dataset/"
    "tiger-line-shapefile-2025-nation-u-s-state-and-equivalent-entities"
)


def parse_bbox(value: Sequence[float] | str) -> tuple[float, float, float, float]:
    """Phân tích và xác thực bbox theo thứ tự kinh độ Tây, vĩ độ Nam, Đông, Bắc."""
    try:
        bbox = tuple(float(part.strip()) for part in value.split(",")) if isinstance(
            value, str
        ) else tuple(float(part) for part in value)
    except (TypeError, ValueError) as exc:
        raise ValueError("bbox phải gồm bốn số: kinh độ Tây, vĩ độ Nam, Đông, Bắc.") from exc

    if len(bbox) != 4 or not all(math.isfinite(part) for part in bbox):
        raise ValueError("bbox phải gồm đúng bốn số hữu hạn.")
    west, south, east, north = bbox
    if not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
        raise ValueError("bbox nằm ngoài phạm vi tọa độ hợp lệ hoặc có thứ tự sai.")
    return west, south, east, north


def parse_bboxes(value: Any) -> list[tuple[float, float, float, float]]:
    """Chuẩn hóa một bbox hoặc danh sách bbox."""
    if isinstance(value, str):
        return [parse_bbox(value)]
    if isinstance(value, Mapping):
        return [parse_bbox(bbox) for bbox in value.values()]
    if isinstance(value, Sequence) and len(value) == 4 and all(
        isinstance(part, (int, float)) for part in value
    ):
        return [parse_bbox(value)]
    if not isinstance(value, Sequence) or not value:
        raise ValueError("Cần khai báo ít nhất một bbox.")
    return [parse_bbox(item) for item in value]


def load_config(path: Path) -> dict[str, Any]:
    """Đọc và kiểm tra các trường cấu hình cần cho lần thu thập."""
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            "Chưa cài PyYAML. Chạy lệnh: python -m pip install -r requirements.txt"
        ) from exc

    config_bytes = path.read_bytes()
    config = yaml.safe_load(config_bytes.decode("utf-8"))
    if not isinstance(config, dict):
        raise ValueError(f"Cấu hình nguồn không phải YAML mapping: {path}")
    config["_config_path"] = path.as_posix()
    config["_config_sha256"] = hashlib.sha256(config_bytes).hexdigest()

    region = config.get("region")
    themes = config.get("themes")
    acquisition = config.get("acquisition")
    if not isinstance(region, dict):
        raise ValueError("Cấu hình cần có mục region.")
    raw_bboxes = region.get("prefilter_bboxes_wsen")
    if raw_bboxes is None:
        raise ValueError("Cấu hình cần có region.prefilter_bboxes_wsen.")
    if not isinstance(acquisition, dict) or "raw_path_template" not in acquisition:
        raise ValueError("Cấu hình cần có acquisition.raw_path_template.")
    if not isinstance(region.get("boundary"), dict):
        raise ValueError("Cấu hình cần có ranh giới Hoa Kỳ trong region.boundary.")
    if not isinstance(themes, dict) or not isinstance(themes.get("types"), dict):
        raise ValueError("Cấu hình cần khai báo themes.types.")
    if isinstance(raw_bboxes, Mapping):
        config["region"]["bbox_names"] = list(raw_bboxes)
    config["region"]["prefilter_bboxes_wsen"] = parse_bboxes(raw_bboxes)
    config["themes"]["selected"] = validate_themes(
        themes.get("selected", []), themes["types"]
    )
    return config


def validate_themes(selected: Sequence[str], theme_types: Mapping[str, Any]) -> list[str]:
    """Xác thực danh sách theme trước khi lập kế hoạch."""
    if isinstance(selected, str):
        raise ValueError("Danh sách theme phải là các giá trị riêng, không phải một chuỗi.")
    themes = list(dict.fromkeys(str(theme).strip().lower() for theme in selected))
    if not themes:
        raise ValueError("Cần chọn ít nhất một theme Overture.")
    unknown = sorted(set(themes) - set(theme_types))
    if unknown:
        raise ValueError(
            f"Theme không hợp lệ: {', '.join(unknown)}. "
            f"Các theme hỗ trợ: {', '.join(sorted(theme_types))}."
        )
    for theme in themes:
        types = theme_types[theme]
        if not isinstance(types, list) or not types or not all(
            isinstance(item, str) and item for item in types
        ):
            raise ValueError(f"Cấu hình feature type không hợp lệ cho theme {theme}.")
    return themes


def validate_release(release: str) -> str:
    """Chặn giá trị phiên bản có thể tạo đường dẫn ngoài thư mục dữ liệu."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", release):
        raise ValueError(f"Mã phiên bản Overture không hợp lệ: {release!r}")
    return release


def resolve_release(requested: str) -> str:
    """Đổi bí danh latest thành phiên bản cụ thể qua catalog STAC chính thức."""
    if requested.lower() != "latest":
        return validate_release(requested)

    try:
        from overturemaps.core import get_latest_release
    except ImportError as exc:
        raise RuntimeError(
            "Chưa cài overturemaps. Chạy lệnh: python -m pip install -r requirements.txt"
        ) from exc

    resolved = get_latest_release()
    if not resolved:
        raise RuntimeError(f"Catalog STAC không trả về phiên bản mới nhất: {STAC_CATALOG_URL}")
    return validate_release(str(resolved))


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ValueError("Tên khu vực không tạo được mã thư mục hợp lệ.")
    return slug


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tool_provenance() -> dict[str, str]:
    tool_path = Path(__file__).resolve()
    return {
        "path": tool_path.as_posix(),
        "version": "0.1.0",
        "sha256": _sha256_file(tool_path),
    }


def _package_version() -> str | None:
    try:
        return version("overturemaps")
    except PackageNotFoundError:
        return None


def plan_download(
    config: dict[str, Any],
    requested_release: str,
    output_root: Path,
    selected_themes: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Tạo kế hoạch tải mà chưa đọc dữ liệu feature."""
    release = resolve_release(requested_release)
    region = config["region"]
    region_name = str(region.get("name") or region.get("subdivision") or "region")
    region_slug = _safe_slug(region_name)
    bboxes = parse_bboxes(region["prefilter_bboxes_wsen"])
    bbox_names = region.get("bbox_names") or [
        f"bbox_{index + 1}" for index in range(len(bboxes))
    ]
    themes = validate_themes(
        config["themes"]["selected"]
        if selected_themes is None
        else selected_themes,
        config["themes"]["types"],
    )
    feature_types = [
        {"theme": theme, "type": feature_type}
        for theme in themes
        for feature_type in config["themes"]["types"][theme]
    ]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = (
        output_root
        / f"release={release}"
        / f"region={region_slug}"
        / f"run={run_id}"
    )
    return {
        "source_id": config.get("source_id", "overture_us"),
        "requested_release": requested_release,
        "resolved_release": release,
        "selected_themes": themes,
        "feature_types": feature_types,
        "prefilter_bboxes_wsen": [list(bbox) for bbox in bboxes],
        "areas": [
            {"name": name, "bbox_wsen": list(bbox)}
            for name, bbox in zip(bbox_names, bboxes)
        ],
        "region_name": region_name,
        "run_id": run_id,
        "run_dir": run_dir,
        "manifest_path": run_dir / "run_manifest.json",
        "tool_provenance": _tool_provenance(),
    }


def _stac_bbox_intersects(
    item_bbox: Any, query_bbox: Sequence[float]
) -> bool:
    if isinstance(item_bbox, Mapping):
        west = float(item_bbox["xmin"])
        south = float(item_bbox["ymin"])
        east = float(item_bbox["xmax"])
        north = float(item_bbox["ymax"])
    elif isinstance(item_bbox, Sequence) and len(item_bbox) >= 4:
        west, south, east, north = (float(value) for value in item_bbox[:4])
    else:
        raise ValueError("STAC item thiếu bbox hợp lệ; không thể ước tính dung lượng.")
    query_west, query_south, query_east, query_north = query_bbox
    return (
        west <= query_east
        and east >= query_west
        and south <= query_north
        and north >= query_south
    )


def estimate_stac_items(
    items: Sequence[dict[str, Any]],
    feature_types: Sequence[dict[str, str]],
    query_bboxes: Sequence[Sequence[float]],
) -> dict[str, Any]:
    """Ước tính dung lượng các tệp STAC giao với bbox tiền lọc."""
    selected = {feature["type"] for feature in feature_types}
    totals = {feature_type: 0 for feature_type in selected}
    file_counts = {feature_type: 0 for feature_type in selected}
    for item in items:
        feature_type = str(item.get("collection", ""))
        if feature_type not in selected:
            continue
        item_bbox = item.get("bbox")
        if not item_bbox:
            raise ValueError(
                f"STAC item {feature_type!r} không có bbox; "
                "không thể ước tính tải an toàn."
            )
        if not any(
            _stac_bbox_intersects(item_bbox, query_bbox)
            for query_bbox in query_bboxes
        ):
            continue

        aws_asset = (item.get("assets") or {}).get("aws") or {}
        size = aws_asset.get("file:size")
        if size is None:
            raise ValueError(
                f"STAC item {feature_type!r} thiếu assets.aws.file:size."
            )
        size = int(size)
        if size < 0:
            raise ValueError("STAC trả về kích thước tệp âm.")
        totals[feature_type] += size
        file_counts[feature_type] += 1

    return {
        "method": "Tổng file:size STAC của các item giao bbox; đây là ước tính bảo thủ.",
        "bytes_by_type": totals,
        "files_by_type": file_counts,
        "candidate_bytes": sum(totals.values()),
        "candidate_files": sum(file_counts.values()),
    }


def fetch_stac_estimate(plan: dict[str, Any]) -> dict[str, Any]:
    """Đọc index STAC của release để ước tính mà không tải GeoParquet."""
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise RuntimeError(
            "Cần PyArrow để đọc index STAC. "
            "Chạy lệnh: python -m pip install -r requirements-dev.txt"
        ) from exc

    index_url = (
        f"https://stac.overturemaps.org/{plan['resolved_release']}/collections.parquet"
    )
    request = Request(index_url, headers={"User-Agent": "DATA-2026/0.1 (STAC size plan)"})
    with urlopen(request, timeout=120) as response:
        index_bytes = response.read()
    table = parquet.read_table(
        io.BytesIO(index_bytes),
        columns=["collection", "bbox", "assets"],
    )
    estimate = estimate_stac_items(
        table.to_pylist(),
        plan["feature_types"],
        plan["prefilter_bboxes_wsen"],
    )
    estimate.update(
        {
            "index_url": index_url,
            "index_bytes_read": len(index_bytes),
        }
    )
    return estimate


def available_disk_bytes(path: Path) -> int:
    """Lấy dung lượng trống tại thư mục hiện có gần nhất."""
    probe = path
    while not probe.exists():
        parent = probe.parent
        if parent == probe:
            raise OSError(f"Không tìm được thư mục để kiểm tra dung lượng: {path}")
        probe = parent
    return shutil.disk_usage(probe).free


def _validate_census_geojson(
    payload: dict[str, Any], included_codes: set[str]
) -> list[dict[str, Any]]:
    if payload.get("type") != "FeatureCollection":
        raise ValueError("TIGERweb không trả về GeoJSON FeatureCollection.")
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("GeoJSON Census thiếu danh sách features.")

    found_codes: set[str] = set()
    for feature in features:
        properties = feature.get("properties") or {}
        statefp = str(properties.get("GEOID", "")).zfill(2)
        if statefp not in included_codes:
            raise ValueError(f"TIGERweb trả về FIPS ngoài cấu hình: {statefp!r}.")
        if statefp in found_codes:
            raise ValueError(f"TIGERweb trả về FIPS trùng lặp: {statefp}.")
        if not isinstance(feature.get("geometry"), dict):
            raise ValueError(f"GeoJSON thiếu hình học cho FIPS {statefp}.")
        found_codes.add(statefp)

    missing_codes = sorted(included_codes - found_codes)
    if missing_codes:
        raise RuntimeError(
            "Thiếu đơn vị địa lý trong TIGERweb: " + ", ".join(missing_codes)
        )
    return features


def _fetch_census_geojson(boundary: dict[str, Any]) -> dict[str, Any]:
    included_codes = [str(code).zfill(2) for code in boundary["included_statefp"]]
    features: list[dict[str, Any]] = []
    total_bytes = 0
    for offset in range(0, len(included_codes), 8):
        code_batch = included_codes[offset : offset + 8]
        where = " OR ".join(f"GEOID = '{code}'" for code in code_batch)
        form = {
            "where": where,
            "outFields": "GEOID,NAME,STUSAB",
            "returnGeometry": "true",
            "outSR": boundary["target_crs"].split(":")[-1],
            "f": "geojson",
        }
        request = Request(
            boundary["url"],
            data=urlencode(form).encode("utf-8"),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "DATA-2026/0.1 (Census TIGERweb boundary)",
            },
            method="POST",
        )
        with urlopen(request, timeout=120) as response:
            response_bytes = response.read(100_000_001)
        total_bytes += len(response_bytes)
        if total_bytes > 100_000_000:
            raise RuntimeError("GeoJSON ranh giới Census vượt giới hạn 100 MB.")
        if len(response_bytes) >= 100_000_001:
            raise RuntimeError("Một truy vấn TIGERweb vượt giới hạn 100 MB.")
        result = json.loads(response_bytes)
        _validate_census_geojson(result, set(code_batch))
        features.extend(result["features"])

    payload = {"type": "FeatureCollection", "features": features}
    _validate_census_geojson(payload, set(included_codes))
    return payload


def download_census_boundary(config: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    """Tải GeoJSON ranh giới Census TIGERweb đã ghim phiên bản."""
    boundary = config["region"]["boundary"]
    boundary_path = Path(boundary["boundary_path"])
    manifest_path = boundary_path.with_suffix(boundary_path.suffix + ".manifest.json")
    boundary_path.parent.mkdir(parents=True, exist_ok=True)
    previous_manifest: dict[str, Any] = {}
    if manifest_path.is_file():
        try:
            previous_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous_manifest = {}
    retrieved_at = previous_manifest.get("retrieved_at_utc")

    if not boundary_path.exists():
        partial_path = boundary_path.with_name(
            f"{boundary_path.name}.partial-{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}"
        )
        try:
            geojson = _fetch_census_geojson(boundary)
            partial_path.write_text(
                json.dumps(geojson, ensure_ascii=False, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            _validate_census_geojson(
                geojson, {str(code).zfill(2) for code in boundary["included_statefp"]}
            )
            partial_path.rename(boundary_path)
            retrieved_at = datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            _write_json(
                manifest_path,
                {
                    "status": "failed",
                    "source_id": boundary["source_id"],
                    "source_url": boundary["url"],
                    "failed_at_utc": datetime.now(timezone.utc).isoformat(),
                    "error_type": type(exc).__name__,
                    "error": str(exc)[:2000],
                    "partial_path": partial_path.as_posix()
                    if partial_path.exists()
                    else None,
                },
            )
            raise

    try:
        payload = json.loads(boundary_path.read_text(encoding="utf-8"))
        features = _validate_census_geojson(
            payload, {str(code).zfill(2) for code in boundary["included_statefp"]}
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"GeoJSON ranh giới Census không hợp lệ: {boundary_path}") from exc

    boundary_sha256 = _sha256_file(boundary_path)
    previous_sha256 = previous_manifest.get("sha256")
    if previous_sha256 and previous_sha256 != boundary_sha256:
        raise RuntimeError(
            "Checksum ranh giới Census khác manifest đã có; "
            "không ghi đè hay dùng bản chụp đã thay đổi."
        )
    manifest = {
        "status": "available",
        "source_id": boundary["source_id"],
        "provider": "U.S. Census Bureau",
        "edition": boundary["edition"],
        "layer_id": boundary["layer_id"],
        "source_url": boundary["url"],
        "documentation_url": boundary.get(
            "documentation_url", CENSUS_BOUNDARY_DOCS_URL
        ),
        "query": {
            "out_fields": ["GEOID", "NAME", "STUSAB"],
            "output_format": "GeoJSON",
            "output_crs": boundary["target_crs"],
            "included_statefp": boundary["included_statefp"],
        },
        "retrieved_at_utc": retrieved_at,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "boundary_path": boundary_path.as_posix(),
        "feature_count": len(features),
        "bytes": boundary_path.stat().st_size,
        "sha256": boundary_sha256,
        "source_crs": boundary["source_crs"],
        "target_crs": boundary["target_crs"],
        "included_statefp": boundary["included_statefp"],
        "license_review_state": "pending_source_terms_review",
    }
    _write_json(manifest_path, manifest)
    return boundary_path, manifest


def load_us_boundary(config: dict[str, Any], boundary_path: Path) -> Any:
    """Hợp nhất các đơn vị Census đã cấu hình trong GeoJSON EPSG:4326."""
    try:
        import shapely
        from shapely.geometry import shape
        from shapely.ops import unary_union
    except ImportError as exc:
        raise RuntimeError(
            "Thiếu Shapely. Chạy lệnh: python -m pip install -r requirements.txt"
        ) from exc

    included_codes = {
        str(code).zfill(2) for code in config["region"]["boundary"]["included_statefp"]
    }
    payload = json.loads(boundary_path.read_text(encoding="utf-8"))
    features = _validate_census_geojson(payload, included_codes)
    polygons = [shape(feature["geometry"]) for feature in features]
    boundary = unary_union(polygons)
    if boundary.is_empty or not boundary.is_valid:
        raise RuntimeError("Ranh giới Hoa Kỳ hợp nhất bị rỗng hoặc không hợp lệ.")
    return shapely.force_2d(boundary)


def _filtered_reader(
    readers: list[Any], boundary: Any, counters: dict[str, int]
) -> Any:
    """Tạo Arrow reader chỉ giữ feature có toàn bộ geometry nằm trong Hoa Kỳ."""
    try:
        import pyarrow as pa
        import shapely
    except ImportError as exc:
        raise RuntimeError(
            "Thiếu PyArrow hoặc Shapely. Chạy lệnh: "
            "python -m pip install -r requirements.txt"
        ) from exc

    schema = readers[0].schema
    geometry_index = schema.get_field_index("geometry")
    if geometry_index < 0:
        raise ValueError("Feature type Overture không có trường geometry.")

    def batches():
        for reader in readers:
            for batch in reader:
                if batch.schema != schema:
                    raise ValueError(
                        "Schema của các bbox không đồng nhất trong cùng feature type."
                    )
                counters["candidate_rows"] += batch.num_rows
                values = batch.column(geometry_index).to_pylist()
                wkbs = [
                    bytes(value)
                    if isinstance(value, (bytes, bytearray, memoryview))
                    else None
                    for value in values
                ]
                geometries = shapely.from_wkb(wkbs)
                covered = shapely.covered_by(geometries, boundary)
                keep = [bool(value) if value is not None else False for value in covered]
                counters["us_rows"] += sum(keep)
                if any(keep):
                    yield batch.filter(pa.array(keep, type=pa.bool_()))

    return pa.RecordBatchReader.from_batches(schema, batches())


def download_feature_type(
    config: dict[str, Any],
    plan: dict[str, Any],
    feature: dict[str, str],
    boundary: Any,
    boundary_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Tải một feature type theo bbox, rồi giữ nguyên các feature hoàn toàn thuộc US."""
    try:
        from overturemaps import record_batch_reader
        from overturemaps.core import StacIndexWarning
        from overturemaps.writers import copy, get_writer
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise RuntimeError(
            "Thiếu dependency tải Overture. Chạy lệnh: "
            "python -m pip install -r requirements.txt"
        ) from exc

    theme, feature_type = feature["theme"], feature["type"]
    type_dir = (
        plan["run_dir"]
        / f"theme={theme}"
        / f"type={feature_type}"
    )
    output_path = type_dir / f"{feature_type}.geoparquet"
    partial_path = type_dir / f"{feature_type}.partial.geoparquet"
    manifest_path = type_dir / "manifest.json"
    type_dir.mkdir(parents=True, exist_ok=False)

    counters = {"candidate_rows": 0, "us_rows": 0}
    type_manifest: dict[str, Any] = {
        "status": "running",
        "source_id": plan["source_id"],
        "provider": "Overture Maps Foundation",
        "theme": theme,
        "feature_type": feature_type,
        "requested_release": plan["requested_release"],
        "resolved_release": plan["resolved_release"],
        "release_catalog_url": STAC_CATALOG_URL,
        "source_data_url": (
            "s3://overturemaps-us-west-2/"
            f"release/{plan['resolved_release']}/theme={theme}/type={feature_type}/"
        ),
        "documentation_url": OVERTURE_PY_DOCS_URL,
        "config_path": config.get("_config_path"),
        "config_sha256": config.get("_config_sha256"),
        "tool_provenance": plan["tool_provenance"],
        "boundary_manifest": boundary_manifest,
        "filter_policy": "geometry_fully_covered_by_us_boundary",
        "prefilter_bboxes_wsen": plan["prefilter_bboxes_wsen"],
        "areas": plan["areas"],
        "region_name": plan["region_name"],
        "region_coverage": config["region"].get("coverage"),
        "accessed_at_utc": datetime.now(timezone.utc).isoformat(),
        "overturemaps_client_version": _package_version(),
        "license_review_state": config.get("license_review", {}).get(
            "state", "unknown"
        ),
        "license_documentation": {
            "common": config.get("license_review", {}).get(
                "common_documentation", []
            ),
            "theme": config.get("license_review", {})
            .get("documentation_by_theme", {})
            .get(theme),
        },
        "commercial_redistribution_approved": config.get("license_review", {}).get(
            "commercial_redistribution_approved", False
        ),
        "attribution_required": config.get("license_review", {}).get(
            "attribution_required"
        ),
        "candidate_rows": 0,
        "us_rows": 0,
        "excluded_by_boundary_policy": 0,
        "estimated_candidate_bytes": plan.get("size_estimate", {})
        .get("bytes_by_type", {})
        .get(feature_type),
        "output_path": output_path.as_posix(),
    }
    _write_json(manifest_path, type_manifest)

    try:
        readers = []
        with warnings.catch_warnings():
            # STAC lỗi phải dừng; không âm thầm quét toàn bộ dữ liệu toàn cầu.
            warnings.simplefilter("error", StacIndexWarning)
            for bbox in plan["prefilter_bboxes_wsen"]:
                reader = record_batch_reader(
                    feature_type,
                    bbox=tuple(bbox),
                    release=plan["resolved_release"],
                    stac=True,
                )
                if reader is not None:
                    readers.append(reader)

        if not readers:
            type_manifest.update(
                {
                    "status": "no_candidates",
                    "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                    "output_path": None,
                }
            )
            _write_json(manifest_path, type_manifest)
            return type_manifest

        filtered = _filtered_reader(readers, boundary, counters)
        with get_writer("geoparquet", str(partial_path), schema=filtered.schema) as writer:
            copy(filtered, writer)

        type_manifest.update(
            {
                "status": "completed",
                "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                "candidate_rows": counters["candidate_rows"],
                "us_rows": counters["us_rows"],
                "excluded_by_boundary_policy": (
                    counters["candidate_rows"] - counters["us_rows"]
                ),
                "output_bytes": partial_path.stat().st_size
                if partial_path.exists()
                else 0,
                "sha256": _sha256_file(partial_path)
                if partial_path.is_file()
                else None,
                "row_count": parquet.ParquetFile(partial_path).metadata.num_rows
                if partial_path.is_file() and counters["us_rows"]
                else 0,
                "output_path": output_path.as_posix()
                if counters["us_rows"]
                else None,
            }
        )
        if counters["us_rows"]:
            partial_path.rename(output_path)
        _write_json(manifest_path, type_manifest)
        return type_manifest
    except Exception as exc:
        type_manifest.update(
            {
                "status": "failed",
                "failed_at_utc": datetime.now(timezone.utc).isoformat(),
                "candidate_rows": counters["candidate_rows"],
                "us_rows": counters["us_rows"],
                "excluded_by_boundary_policy": (
                    counters["candidate_rows"] - counters["us_rows"]
                ),
                "error_type": type(exc).__name__,
                "error": str(exc)[:2000],
                "partial_path": partial_path.as_posix()
                if partial_path.exists()
                else None,
            }
        )
        _write_json(manifest_path, type_manifest)
        raise


def download_us_datasets(
    config: dict[str, Any], plan: dict[str, Any]
) -> dict[str, Any]:
    """Tải các theme đã chọn và chỉ lưu geometry nằm hoàn toàn trong US."""
    run_dir: Path = plan["run_dir"]
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, Any] = {
        "status": "running",
        "source_id": plan["source_id"],
        "requested_release": plan["requested_release"],
        "resolved_release": plan["resolved_release"],
        "selected_themes": plan["selected_themes"],
        "feature_types": plan["feature_types"],
        "region": plan["region_name"],
        "region_coverage": config["region"].get("coverage"),
        "prefilter_bboxes_wsen": plan["prefilter_bboxes_wsen"],
        "areas": plan["areas"],
        "boundary_source_id": config["region"]["boundary"]["source_id"],
        "boundary_filter_policy": "geometry_fully_covered_by_union",
        "size_estimate": plan.get("size_estimate"),
        "free_disk_bytes_at_plan": plan.get("free_disk_bytes"),
        "required_free_disk_bytes": plan.get("required_free_disk_bytes"),
        "config_path": config.get("_config_path"),
        "config_sha256": config.get("_config_sha256"),
        "tool_provenance": plan["tool_provenance"],
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "datasets": [],
    }
    _write_json(plan["manifest_path"], manifest)

    try:
        boundary_path, boundary_manifest = download_census_boundary(config)
        manifest["boundary_manifest"] = boundary_manifest
        _write_json(plan["manifest_path"], manifest)
        us_boundary = load_us_boundary(config, boundary_path)
        for feature in plan["feature_types"]:
            try:
                result = download_feature_type(
                    config,
                    plan,
                    feature,
                    us_boundary,
                    boundary_manifest,
                )
            except Exception:
                manifest["datasets"].append(
                    {
                        **feature,
                        "status": "failed",
                        "manifest_path": (
                            plan["run_dir"]
                            / f"theme={feature['theme']}"
                            / f"type={feature['type']}"
                            / "manifest.json"
                        ).as_posix(),
                    }
                )
                _write_json(plan["manifest_path"], manifest)
                raise
            manifest["datasets"].append(result)
            _write_json(plan["manifest_path"], manifest)
        manifest.update(
            {
                "status": "completed",
                "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
        _write_json(plan["manifest_path"], manifest)
        return manifest
    except Exception as exc:
        manifest.update(
            {
                "status": "failed",
                "failed_at_utc": datetime.now(timezone.utc).isoformat(),
                "error_type": type(exc).__name__,
                "error": str(exc)[:2000],
            }
        )
        _write_json(plan["manifest_path"], manifest)
        raise


def check_download_dependencies(
    config: dict[str, Any], features: list[dict[str, str]]
) -> None:
    """Kiểm tra đủ package trước khi bắt đầu tải ranh giới hoặc Overture."""
    try:
        for module in (
            "pyarrow.parquet",
            "shapely",
            "overturemaps",
            "overturemaps.core",
            "overturemaps.writers",
        ):
            import_module(module)
        core = import_module("overturemaps.core")
    except ImportError as exc:
        raise RuntimeError(
            "Thiếu dependency tải hoặc lọc dữ liệu. "
            "Chạy lệnh: python -m pip install -r requirements-dev.txt"
        ) from exc
    type_theme_map = getattr(core, "type_theme_map", None)
    if not isinstance(type_theme_map, dict):
        raise RuntimeError("Thư viện Overture không cung cấp bảng feature type/theme.")
    for feature in features:
        if type_theme_map.get(feature["type"]) != feature["theme"]:
            raise ValueError(
                f"Feature type {feature['type']} không thuộc theme "
                f"{feature['theme']} theo thư viện Overture đang cài."
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Lập kế hoạch hoặc tải các theme Overture đã chọn trong ranh giới Hoa Kỳ. "
            "Mặc định chỉ lập kế hoạch, không tải dữ liệu."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/data_sources/overture_us.yaml"),
        help="Đường dẫn cấu hình nguồn Overture Hoa Kỳ.",
    )
    parser.add_argument(
        "--release",
        help="Phiên bản Overture cụ thể hoặc latest; mặc định lấy từ cấu hình.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        help="Thư mục gốc lưu dữ liệu; mặc định lấy từ cấu hình.",
    )
    parser.add_argument(
        "--themes",
        help="Danh sách theme phân tách bằng dấu phẩy; mặc định lấy từ cấu hình.",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Thực sự truy cập mạng, tải ranh giới và GeoParquet; nếu bỏ qua chỉ lập kế hoạch.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        acquisition = config["acquisition"]
        requested_release = args.release or str(config.get("release", "latest"))
        output_root = args.output_root or Path(acquisition["raw_root"])
        selected_themes = None
        if args.themes:
            selected_themes = [
                theme.strip().lower()
                for theme in args.themes.split(",")
                if theme.strip()
            ]
        plan = plan_download(config, requested_release, output_root, selected_themes)
        print(f"Phiên bản được yêu cầu: {plan['requested_release']}")
        print(f"Phiên bản sẽ dùng: {plan['resolved_release']}")
        print(f"Phạm vi: {plan['region_name']} — lọc theo polygon Census")
        print(f"Theme đã chọn: {', '.join(plan['selected_themes'])}")
        print(
            "Feature type: "
            + ", ".join(
                f"{item['theme']}/{item['type']}" for item in plan["feature_types"]
            )
        )
        print(f"Đường dẫn dự kiến: {plan['run_dir']}")
        size_estimate = fetch_stac_estimate(plan)
        plan["size_estimate"] = size_estimate
        plan["free_disk_bytes"] = available_disk_bytes(output_root)
        plan["required_free_disk_bytes"] = (
            int(size_estimate["candidate_bytes"] * 1.25) + 50_000_000
        )
        print(
            "Ước tính bảo thủ từ STAC: "
            f"{size_estimate['candidate_bytes']:,} byte "
            f"({size_estimate['candidate_files']:,} tệp ứng viên)."
        )
        for feature in plan["feature_types"]:
            feature_type = feature["type"]
            print(
                f"  {feature['theme']}/{feature_type}: "
                f"{size_estimate['files_by_type'][feature_type]:,} tệp, "
                f"{size_estimate['bytes_by_type'][feature_type]:,} byte"
            )
        print(f"Dung lượng đĩa trống: {plan['free_disk_bytes']:,} byte")
        print(
            "Mức trống tối thiểu đề nghị (ước tính + dự phòng): "
            f"{plan['required_free_disk_bytes']:,} byte"
        )
        if not args.download:
            print(
                "Chưa tải GeoParquet. Kế hoạch chỉ đọc STAC metadata; "
                "thêm --download để xác nhận tải."
            )
            return 0

        if plan["free_disk_bytes"] < plan["required_free_disk_bytes"]:
            parser.error(
                "Dung lượng đĩa trống thấp hơn mức dự phòng. "
                "Giải phóng dung lượng hoặc thu hẹp danh sách theme."
            )
        check_download_dependencies(config, plan["feature_types"])
        manifest = download_us_datasets(config, plan)
        rows = sum(item.get("us_rows", 0) for item in manifest["datasets"])
        size = sum(item.get("output_bytes", 0) for item in manifest["datasets"])
        print(f"Đã lưu {rows:,} feature thuộc Hoa Kỳ, tổng {size:,} byte.")
        print(f"Manifest: {plan['manifest_path']}")
        return 0
    except Exception as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
