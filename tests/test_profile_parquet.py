from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from tools.download_overture_us import (
    _filtered_reader,
    available_disk_bytes,
    build_parser as build_download_parser,
    estimate_stac_items,
    load_config,
    load_us_boundary,
    parse_bbox,
    plan_download,
    validate_themes,
)
from tools.report_overture_places_spike import generate_report
from tools.profile_parquet import (
    build_parser,
    is_list_type,
    is_string_type,
    profile_files,
    quote_identifier,
    resolve_inputs,
    sql_literal,
)


class ProfileHelpersTest(unittest.TestCase):
    def test_sql_quoting_escapes_embedded_quotes(self) -> None:
        self.assertEqual(quote_identifier('field"name'), '"field""name"')
        self.assertEqual(sql_literal("it's data"), "'it''s data'")

    def test_type_detection(self) -> None:
        self.assertTrue(is_list_type("VARCHAR[]"))
        self.assertTrue(is_list_type("LIST(INTEGER)"))
        self.assertFalse(is_list_type("VARCHAR"))
        self.assertTrue(is_string_type("VARCHAR"))
        self.assertFalse(is_string_type("VARCHAR[]"))
        self.assertFalse(is_string_type("INTEGER"))

    def test_help_text_is_vietnamese(self) -> None:
        help_text = build_parser().format_help()
        self.assertIn("Tệp Parquet cục bộ", help_text)
        self.assertIn("Thư mục lưu", help_text)
        download_help = build_download_parser().format_help()
        self.assertIn("theme", download_help)
        self.assertIn("không tải dữ liệu", download_help)

    def test_resolve_inputs_from_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "a.parquet").touch()
            (root / "c.geoparquet").touch()
            (root / "ignore.csv").touch()
            nested = root / "nested"
            nested.mkdir()
            (nested / "b.parquet").touch()
            self.assertEqual(
                [path.name for path in resolve_inputs(str(root))],
                ["a.parquet", "c.geoparquet", "b.parquet"],
            )

    def test_rejects_remote_input(self) -> None:
        with self.assertRaises(ValueError):
            resolve_inputs("s3://bucket/file.parquet")

    def test_bbox_validation(self) -> None:
        self.assertEqual(
            parse_bbox("-106.65,25.84,-93.51,36.50"),
            (-106.65, 25.84, -93.51, 36.5),
        )
        with self.assertRaises(ValueError):
            parse_bbox("-93, 25, -106, 36")

    def test_plan_pins_an_explicit_release_without_network(self) -> None:
        config = {
            "source_id": "overture_us",
            "region": {
                "name": "us_census_state_equivalents",
                "prefilter_bboxes_wsen": [
                    [-125.0, 24.0, -66.0, 49.5],
                    [-180.0, 51.0, -129.0, 72.0],
                    [-161.0, 18.0, -154.0, 23.0],
                ],
            },
            "themes": {
                "selected": ["places"],
                "types": {
                    "places": ["place"],
                    "buildings": ["building", "building_part"],
                },
            },
        }
        plan = plan_download(
            config,
            "2026-10-21.0",
            Path("data/raw/overture"),
            ["places", "buildings"],
        )
        self.assertEqual(plan["resolved_release"], "2026-10-21.0")
        self.assertEqual(len(plan["prefilter_bboxes_wsen"]), 3)
        self.assertEqual(plan["selected_themes"], ["places", "buildings"])
        self.assertEqual(len(plan["feature_types"]), 3)
        self.assertIn("release=2026-10-21.0", plan["run_dir"].as_posix())

    @unittest.skipUnless(importlib.util.find_spec("yaml"), "Chưa cài PyYAML")
    def test_overture_config_uses_latest_and_bounded_region(self) -> None:
        config_path = Path(__file__).parents[1] / "configs/data_sources/overture_us.yaml"
        config = load_config(config_path)
        self.assertEqual(config["release"], "latest")
        self.assertEqual(len(config["region"]["prefilter_bboxes_wsen"]), 6)
        self.assertIn("buildings", config["themes"]["types"])
        self.assertEqual(config["themes"]["selected"], ["places"])
        self.assertGreater(len(config["region"]["boundary"]["included_statefp"]), 50)
        self.assertFalse(config["license_review"]["commercial_redistribution_approved"])

    def test_theme_selection_rejects_unknown_theme(self) -> None:
        with self.assertRaises(ValueError):
            validate_themes(["places", "made_up"], {"places": ["place"]})
        with self.assertRaises(ValueError):
            validate_themes([], {"places": ["place"]})

    def test_stac_size_estimate_counts_only_intersecting_selected_types(self) -> None:
        items = [
            {
                "collection": "place",
                "bbox": {"xmin": -100, "ymin": 30, "xmax": -90, "ymax": 40},
                "assets": {"aws": {"file:size": 100}},
            },
            {
                "collection": "place",
                "bbox": {"xmin": 10, "ymin": 30, "xmax": 20, "ymax": 40},
                "assets": {"aws": {"file:size": 900}},
            },
            {
                "collection": "building",
                "bbox": {"xmin": -100, "ymin": 30, "xmax": -90, "ymax": 40},
                "assets": {"aws": {"file:size": 200}},
            },
        ]
        estimate = estimate_stac_items(
            items,
            [{"theme": "places", "type": "place"}],
            [[-125, 24, -66, 50]],
        )
        self.assertEqual(estimate["candidate_bytes"], 100)
        self.assertEqual(estimate["files_by_type"], {"place": 1})

    def test_disk_check_uses_existing_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            self.assertGreater(
                available_disk_bytes(Path(temporary) / "not-created" / "yet"),
                0,
            )

    @unittest.skipUnless(
        importlib.util.find_spec("pyarrow") and importlib.util.find_spec("shapely"),
        "Chưa cài PyArrow/Shapely",
    )
    def test_us_filter_keeps_only_geometries_fully_inside_boundary(self) -> None:
        import pyarrow as pa
        from shapely.geometry import Point, Polygon

        schema = pa.schema(
            [("id", pa.int64()), ("geometry", pa.binary())]
        )
        batch = pa.RecordBatch.from_arrays(
            [
                pa.array([1, 2, 3]),
                pa.array(
                    [
                        Point(0.5, 0.5).wkb,
                        Point(2, 2).wkb,
                        Point(1, 0.5).wkb,
                    ],
                    type=pa.binary(),
                ),
            ],
            schema=schema,
        )
        reader = pa.RecordBatchReader.from_batches(schema, [batch])
        counters = {"candidate_rows": 0, "us_rows": 0}
        filtered = _filtered_reader(
            [reader],
            Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
            counters,
        )
        self.assertEqual(filtered.read_all()["id"].to_pylist(), [1, 3])
        self.assertEqual(counters, {"candidate_rows": 3, "us_rows": 2})

    @unittest.skipUnless(
        importlib.util.find_spec("shapely"),
        "Chưa cài Shapely",
    )
    def test_census_boundary_includes_only_configured_state_codes(self) -> None:
        from shapely.geometry import Point

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            boundary_path = root / "states.geojson"
            polygon = {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
            }
            boundary_path.write_text(
                json.dumps(
                    {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "properties": {"GEOID": "01", "NAME": "State 01"},
                                "geometry": polygon,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            config = {
                "region": {
                    "boundary": {
                        "included_statefp": ["01"],
                    }
                }
            }
            boundary = load_us_boundary(config, boundary_path)
            self.assertTrue(boundary.covers(Point(0.5, 0.5)))
            self.assertFalse(boundary.covers(Point(10.5, 10.5)))

    @unittest.skipUnless(importlib.util.find_spec("duckdb"), "Chưa cài DuckDB")
    def test_profile_separates_null_blank_and_empty_list(self) -> None:
        import duckdb

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            parquet_path = root / "fixture.parquet"
            output = root / "report"
            connection = duckdb.connect()
            try:
                connection.execute(
                    "CREATE TABLE fixture (name VARCHAR, tags VARCHAR[])"
                )
                connection.execute(
                    "INSERT INTO fixture VALUES "
                    "('known', ['a']), ('', []), (NULL, NULL)"
                )
                connection.execute(
                    f"COPY fixture TO {sql_literal(parquet_path.as_posix())} "
                    "(FORMAT PARQUET)"
                )
            finally:
                connection.close()

            manifest = profile_files([parquet_path], output, "test-fixture")
            self.assertEqual(manifest["row_count"], 3)
            with (output / "column_profile.csv").open(
                newline="", encoding="utf-8"
            ) as stream:
                rows = {row["column"]: row for row in csv.DictReader(stream)}

            self.assertEqual(rows["name"]["null_count"], "1")
            self.assertEqual(rows["name"]["blank_string_count"], "1")
            self.assertEqual(rows["tags"]["null_count"], "1")
            self.assertEqual(rows["tags"]["empty_list_count"], "1")

    @unittest.skipUnless(importlib.util.find_spec("duckdb"), "Chưa cài DuckDB")
    def test_spike_report_uses_aggregate_fixture_and_checks_manifest_rows(self) -> None:
        import duckdb

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_dir = root / "input"
            input_dir.mkdir()
            parquet_path = input_dir / "places.parquet"
            connection = duckdb.connect()
            try:
                connection.execute(
                    '''CREATE TABLE fixture (
                        id VARCHAR,
                        geometry BLOB,
                        names STRUCT("primary" VARCHAR),
                        categories STRUCT("primary" VARCHAR, alternate VARCHAR[]),
                        addresses STRUCT(
                            freeform VARCHAR,
                            locality VARCHAR,
                            postcode VARCHAR,
                            region VARCHAR,
                            country VARCHAR
                        )[],
                        websites VARCHAR[],
                        phones VARCHAR[],
                        emails VARCHAR[],
                        confidence DOUBLE,
                        operating_status VARCHAR
                    )'''
                )
                connection.execute(
                    '''INSERT INTO fixture VALUES
                    ('id-1', NULL, {'primary':'A'}, {'primary':'food','alternate':['cafe']},
                     [{'freeform':'address','locality':'Town','postcode':'123',
                       'region':'ST','country':'US'}],
                     ['https://example.test'], ['555'], [], 0.9, 'open'),
                    ('id-2', NULL, {'primary':NULL}, {'primary':NULL,'alternate':[]},
                     [{'freeform':NULL,'locality':NULL,'postcode':NULL,
                       'region':NULL,'country':NULL}],
                     [''], [], [], NULL, 'closed')'''
                )
                connection.execute(
                    f"COPY fixture TO {sql_literal(parquet_path.as_posix())} "
                    "(FORMAT PARQUET)"
                )
            finally:
                connection.close()

            run_manifest_path = root / "run_manifest.json"
            run_manifest_path.write_text(
                json.dumps(
                    {
                        "status": "completed",
                        "resolved_release": "fixture-release",
                        "region": "fixture-us",
                        "boundary_manifest": {"edition": 2025, "sha256": "boundary-hash"},
                    }
                ),
                encoding="utf-8",
            )
            type_manifest_path = input_dir / "manifest.json"
            type_manifest_path.write_text(
                json.dumps(
                    {
                        "status": "completed",
                        "row_count": 2,
                        "output_bytes": parquet_path.stat().st_size,
                        "sha256": "snapshot-hash",
                        "candidate_rows": 3,
                        "us_rows": 2,
                        "excluded_by_boundary_policy": 1,
                        "license_review_state": "pending",
                        "commercial_redistribution_approved": False,
                    }
                ),
                encoding="utf-8",
            )

            output_dir = root / "report"
            manifest = generate_report(
                str(input_dir),
                output_dir,
                "Fixture Overture Places",
                run_manifest_path,
                type_manifest_path,
            )
            self.assertEqual(manifest["profile_metrics"]["row_count"], 2)
            self.assertEqual(manifest["profile_metrics"]["duplicate_id_rows"], 0)
            availability = {
                item["field"]: item["available_count"]
                for item in manifest["profile_metrics"]["field_availability"]
            }
            self.assertEqual(availability["category_primary"], 1)
            self.assertEqual(availability["websites"], 1)
            self.assertEqual(availability["addresses"], 2)
            self.assertEqual(availability["address_freeform"], 1)
            self.assertEqual(manifest["profile_metrics"]["geometry"]["status"], "completed")
            self.assertEqual(manifest["profile_metrics"]["geometry"]["null_count"], 2)
            self.assertEqual(
                sum(
                    item["row_count"]
                    for item in manifest["profile_metrics"]["confidence_distribution"]
                ),
                2,
            )
            self.assertTrue((output_dir / "REPORT.md").is_file())
            self.assertTrue((output_dir / "profile" / "column_profile.csv").is_file())
            self.assertTrue((output_dir / "category_profile.csv").is_file())
            self.assertTrue((output_dir / "geometry_profile.json").is_file())
            self.assertTrue((output_dir / "confidence_distribution.csv").is_file())


if __name__ == "__main__":
    unittest.main()
