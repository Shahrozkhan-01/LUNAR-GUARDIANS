"""Tests for the read-only processed NASA dataset API."""

import csv
import gzip
from dataclasses import replace
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.main import app
from app.routes import datasets as dataset_routes
from app.services import dataset_service


class TestDatasetAPI(unittest.TestCase):
    def test_routes_are_registered_and_listing_reports_supported_datasets(self):
        expected_paths = {
            "/api/datasets",
            "/api/datasets/{dataset_id}/metadata",
            "/api/datasets/{dataset_id}/summary",
            "/api/datasets/{dataset_id}/records",
        }
        self.assertTrue(expected_paths.issubset(set(app.openapi()["paths"])))

        result = dataset_routes.datasets_list()
        self.assertEqual(result["dataset_count"], 9)
        self.assertEqual(
            {item["dataset_id"] for item in result["datasets"]},
            {"diviner", "lola", "ace_epam", "stereo_impact", "jpl_horizons", "omni_hourly", "lend", "lro_spice", "osd53"},
        )
        self.assertTrue(
            all(item["availability"]["status"] == "available" for item in result["datasets"])
        )
        self.assertTrue(all(item["category"] for item in result["datasets"]))
        self.assertTrue(all(item["scientific_purpose"] for item in result["datasets"]))
        self.assertTrue(all(item["important_variables"] for item in result["datasets"]))
        self.assertTrue(
            next(item for item in result["datasets"] if item["dataset_id"] == "lola")[
                "record_access"
            ]["available"]
        )

    def test_metadata_includes_sources_units_validation_and_science_limits(self):
        diviner = dataset_routes.dataset_metadata("diviner")
        self.assertEqual(diviner["data_type"], "remote_sensing_observation")
        self.assertIn("K", diviner["units"])
        self.assertIn("PDS", diviner["source"]["organization"])
        self.assertIn("PASSED", diviner["validation_status"])
        self.assertTrue(
            any("not live habitat" in item for item in diviner["scientific_limitations"])
        )
        self.assertEqual(
            len(diviner["processing_metadata"]["columns"]),
            11,
        )

        lola = dataset_routes.dataset_metadata("lola")
        self.assertEqual(lola["data_type"], "derived_topographic_product")
        self.assertTrue(
            any("not detailed landing-hazard" in item for item in lola["scientific_limitations"])
        )
        self.assertEqual(
            lola["processing_metadata"]["elevation_conversion"]["scaling_factor"],
            0.5,
        )
        self.assertEqual(lola["preview_metadata"]["record_count"], 64_800)
        self.assertEqual(lola["preview_metadata"]["sample_stride_pixels"], 16)

        ace = dataset_routes.dataset_metadata("ace_epam")
        self.assertTrue(
            any("not astronaut radiation dose" in item for item in ace["scientific_limitations"])
        )
        self.assertIn("P1", ace["processing_metadata"]["variables"])

        horizons = dataset_routes.dataset_metadata("jpl_horizons")
        self.assertEqual(horizons["data_type"], "computed_ephemeris")
        self.assertTrue(
            any("future epochs" in item for item in horizons["scientific_limitations"])
        )
        self.assertFalse(
            horizons["processing_metadata"]["variables"][
                "two_way_vacuum_light_time_seconds_derived"
            ]["is_direct_horizons_measurement"]
        )

        omni = dataset_routes.dataset_metadata("omni_hourly")
        self.assertEqual(omni["data_type"], "near_earth_spacecraft_observation")
        self.assertIn("km/s", omni["units"])
        self.assertTrue(any("lunar-surface" in item for item in omni["scientific_limitations"]))

        lend = dataset_routes.dataset_metadata("lend")
        self.assertEqual(lend["data_type"], "orbital_lunar_neutron_observation")
        self.assertIn("counts", lend["units"])
        self.assertTrue(any("not astronaut radiation dose" in item for item in lend["scientific_limitations"]))

        spice = dataset_routes.dataset_metadata("lro_spice")
        self.assertEqual(spice["data_type"], "computed_spice_geometry")
        self.assertEqual(spice["processing_metadata"]["reference_frame"], "J2000")
        self.assertIn("computed from NASA NAIF", spice["scientific_limitations"][0])

        osd53 = dataset_routes.dataset_metadata("osd53")
        self.assertEqual(osd53["data_type"], "historical_human_research")
        self.assertEqual(osd53["processing_metadata"]["record_count"], 13)
        self.assertTrue(any("medical diagnosis" in item for item in osd53["scientific_limitations"]))




    def test_summary_routes_return_existing_statistics(self):
        diviner = dataset_routes.dataset_summary("diviner")
        self.assertIn("brightness_temperature_interpretation", diviner["summary"])
        self.assertEqual(
            diviner["summary"]["columns"]["t3"]["valid_count"],
            1_042_843,
        )

        lola = dataset_routes.dataset_summary("lola")
        self.assertEqual(
            lola["summary"]["height_m_relative_to_reference_radius_statistics"][
                "sample_count"
            ],
            16_588_800,
        )
        self.assertIn("extrema_warning", lola["summary"])

        ace = dataset_routes.dataset_summary("ace_epam")
        self.assertEqual(ace["summary"]["record_count"], 277)
        self.assertTrue(
            any("not the lunar surface" in item for item in ace["scientific_limitations"])
        )

        stereo = dataset_routes.dataset_summary("stereo_impact")
        self.assertEqual(stereo["summary"]["channel_count"], 14)

        horizons = dataset_routes.dataset_summary("jpl_horizons")
        self.assertEqual(horizons["summary"]["epoch_count"], 8)
        self.assertIn("computed ephemeris", horizons["summary"]["computation_type"].lower())

        omni = dataset_routes.dataset_summary("omni_hourly")
        self.assertEqual(omni["summary"]["record_count"], 744)
        self.assertTrue(any("dose" in item for item in omni["scientific_limitations"]))

        lend = dataset_routes.dataset_summary("lend")
        self.assertEqual(lend["summary"]["record_count"], 85308)
        self.assertIn("spatial_coverage", lend["summary"])

        spice = dataset_routes.dataset_summary("lro_spice")
        self.assertEqual(spice["summary"]["record_count"], 24)

        osd53 = dataset_routes.dataset_summary("osd53")
        self.assertEqual(osd53["summary"]["sample_count"], 13)
        self.assertFalse(osd53["summary"]["clinical_interpretation"])




    def test_csv_record_pagination_preserves_source_fields(self):
        first = dataset_routes.dataset_records("stereo_impact", page=1, page_size=10)
        second = dataset_routes.dataset_records("stereo_impact", page=2, page_size=10)
        self.assertEqual(first["pagination"]["total_records"], 31)
        self.assertEqual(first["pagination"]["total_pages"], 4)
        self.assertTrue(first["pagination"]["has_next"])
        self.assertEqual(len(first["records"]), 10)
        self.assertEqual(len(second["records"]), 10)
        self.assertIn("intensity_electron_0.7_1.4_MeV", first["records"][0])
        self.assertIn("uncertainty_electron_0.7_1.4_MeV", first["records"][0])
        self.assertEqual(first["records"][0]["record_start_utc"], "2012-03-01T00:00:00Z")

        horizons = dataset_routes.dataset_records("jpl_horizons", page=1, page_size=2)
        self.assertEqual(horizons["pagination"]["total_records"], 8)
        self.assertEqual(horizons["records"][0]["earth_moon_range_km"], "4.0561589143E+05")
        self.assertIn("two_way_vacuum_light_time_seconds_derived", horizons["records"][0])

        omni = dataset_routes.dataset_records("omni_hourly", page=1, page_size=2)
        self.assertEqual(omni["pagination"]["total_records"], 744)
        self.assertEqual(omni["records"][0]["timestamp_utc"], "2020-01-01T00:00:00Z")
        self.assertIn("solar_wind_speed_km_s", omni["records"][0])

        lend = dataset_routes.dataset_records("lend", page=1, page_size=2)
        self.assertEqual(lend["pagination"]["total_records"], 85308)
        self.assertEqual(lend["records"][0]["timestamp_utc"], "2020-01-01T00:00:00Z")
        self.assertIn("csetn_sum_counts", lend["records"][0])

        spice = dataset_routes.dataset_records("lro_spice", page=1, page_size=2)
        self.assertEqual(spice["pagination"]["total_records"], 24)
        self.assertEqual(spice["records"][0]["timestamp_utc"], "2017-09-15T00:00:00Z")
        self.assertIn("distance_from_moon_center_km", spice["records"][0])

        osd53 = dataset_routes.dataset_records("osd53", page=1, page_size=2)
        self.assertEqual(osd53["pagination"]["total_records"], 13)
        self.assertIn("sample_id", osd53["records"][0])
        self.assertNotIn("study_subject", osd53["records"][0])


    def test_ace_records_keep_validity_masks_and_never_report_dose(self):
        response = dataset_routes.dataset_records("ace_epam", page=1, page_size=1)
        self.assertEqual(response["pagination"]["total_records"], 277)
        record = response["records"][0]
        self.assertEqual(record["timestamp_utc"], "2020-01-01T00:00:00.000Z")
        self.assertIn("DE1", record["measurements"])
        self.assertIn("valid", record["measurements"]["DE1"])
        self.assertFalse(record["measurements"]["P1"]["valid"])
        self.assertIn("not astronaut radiation dose", response["scientific_limitations"][1])

    def test_large_grid_record_endpoint_remains_disabled(self):
        with self.assertRaises(HTTPException) as raised:
            dataset_routes.dataset_records("diviner", page=1, page_size=50)
        self.assertEqual(raised.exception.status_code, 409)

    def test_lola_preview_records_are_sampled_and_paginated(self):
        response = dataset_routes.dataset_records("lola", page=2, page_size=20)
        self.assertEqual(response["pagination"]["total_records"], 64_800)
        self.assertEqual(response["pagination"]["total_pages"], 3_240)
        self.assertEqual(len(response["records"]), 20)
        first = response["records"][0]
        self.assertEqual(
            set(first),
            {
                "latitude_center_degrees",
                "longitude_center_degrees",
                "elevation_dn",
                "height_m",
                "planetary_radius_m",
            },
        )
        self.assertEqual(
            float(first["height_m"]),
            int(first["elevation_dn"]) * 0.5,
        )
        self.assertEqual(
            float(first["planetary_radius_m"]),
            float(first["height_m"]) + 1_737_400,
        )

    def test_lola_preview_is_reported_when_full_grid_is_not_deployed(self):
        source_root = (
            dataset_service.DATASETS_ROOT
            / "processed"
            / dataset_service.DATASET_SPECS["lola"].processed_directory
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            preview_root = (
                temporary_root
                / "processed"
                / dataset_service.DATASET_SPECS["lola"].processed_directory
            )
            preview_root.mkdir(parents=True)
            for file_name in (
                "ldem_16_preview.csv",
                "ldem_16_preview_metadata.json",
            ):
                shutil.copyfile(source_root / file_name, preview_root / file_name)

            with patch.object(dataset_service, "DATASETS_ROOT", temporary_root):
                listed = next(
                    item
                    for item in dataset_routes.datasets_list()["datasets"]
                    if item["dataset_id"] == "lola"
                )
                metadata = dataset_routes.dataset_metadata("lola")
                records = dataset_routes.dataset_records("lola", page=1, page_size=1)

        self.assertEqual(listed["availability"]["status"], "preview_available")
        self.assertFalse(listed["availability"]["processed_data"])
        self.assertTrue(listed["availability"]["preview_data"])
        self.assertTrue(listed["record_access"]["available"])
        self.assertTrue(metadata["record_access"]["preview_only"])
        self.assertEqual(records["pagination"]["total_records"], 64_800)

    def test_invalid_ids_and_excessive_page_sizes_are_rejected(self):
        with self.assertRaises(HTTPException) as raised:
            dataset_routes.dataset_metadata("..")
        self.assertEqual(raised.exception.status_code, 404)

        with self.assertRaises(HTTPException) as raised:
            dataset_routes.dataset_records("stereo_impact", page=1, page_size=101)
        self.assertEqual(raised.exception.status_code, 422)

    def test_missing_files_are_reported_without_fabricating_data(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_root = Path(temporary_directory) / "missing"
            with patch.object(dataset_service, "DATASETS_ROOT", missing_root):
                listing = dataset_routes.datasets_list()
                self.assertTrue(
                    all(item["availability"]["status"] == "unavailable"
                        for item in listing["datasets"])
                )
                metadata = dataset_routes.dataset_metadata("ace_epam")
                self.assertFalse(metadata["availability"]["processed_data"])
                self.assertIsNone(metadata["processing_metadata"])
                for call in (
                    lambda: dataset_routes.dataset_summary("ace_epam"),
                    lambda: dataset_routes.dataset_records(
                        "stereo_impact", page=1, page_size=50
                    ),
                ):
                    with self.assertRaises(HTTPException) as raised:
                        call()
                    self.assertEqual(raised.exception.status_code, 503)

    def test_empty_csv_dataset_returns_empty_page_with_zero_totals(self):
        spec = dataset_service.DATASET_SPECS["stereo_impact"]
        empty_spec = replace(spec, data_file="empty.csv.gz")
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch.object(dataset_service, "DATASETS_ROOT", Path(temporary_directory)):
                with patch.dict(
                    dataset_service.DATASET_SPECS,
                    {"stereo_impact": empty_spec},
                ):
                    dataset_dir = (
                        Path(temporary_directory)
                        / "processed"
                        / empty_spec.processed_directory
                    )
                    dataset_dir.mkdir(parents=True)
                    with gzip.open(
                        dataset_dir / empty_spec.data_file,
                        "wt",
                        encoding="utf-8",
                        newline="",
                    ) as stream:
                        csv.writer(stream).writerow(["record_start_utc", "measurement"])

                    response = dataset_routes.dataset_records(
                        "stereo_impact", page=1, page_size=20
                    )
        self.assertEqual(response["records"], [])
        self.assertEqual(response["pagination"]["total_records"], 0)
        self.assertEqual(response["pagination"]["total_pages"], 0)
        self.assertFalse(response["pagination"]["has_next"])


if __name__ == "__main__":
    unittest.main()
