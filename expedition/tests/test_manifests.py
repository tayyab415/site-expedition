import copy
import unittest

from expedition.manifests import (
    ALLOWED_MIREYE_FIELDS,
    ManifestValidationError,
    list_reviewed_manifests,
    load_reviewed_manifest,
    validate_manifest,
)


def reviewed_payload():
    return load_reviewed_manifest("logistics-resilience").to_dict()


class CustomManifestTests(unittest.TestCase):
    def test_reviewed_manifest_loads_and_exposes_plan_overrides(self):
        manifest = load_reviewed_manifest("logistics-resilience")

        self.assertEqual(manifest.manifest_version, "1.0.0")
        self.assertTrue(set(manifest.fields) <= ALLOWED_MIREYE_FIELDS)
        self.assertIn("screen-site-core", manifest.skills)
        self.assertIn("route_time", manifest.gaps)
        self.assertEqual(
            list_reviewed_manifests()[0]["manifest_id"], "logistics-resilience"
        )
        overrides = manifest.plan_overrides()
        overrides["fields"].append("not-reviewed")
        self.assertNotIn("not-reviewed", manifest.fields)

    def test_loader_accepts_registry_ids_not_paths(self):
        for unreviewed in (
            "../manifests/logistics-resilience.v1.json",
            "/tmp/custom.json",
            "https://example.test/manifest.json",
            "unknown",
        ):
            with self.subTest(unreviewed=unreviewed):
                with self.assertRaisesRegex(ManifestValidationError, "not reviewed"):
                    load_reviewed_manifest(unreviewed)

    def test_rejects_unknown_skill_and_source_discovery(self):
        payload = reviewed_payload()
        self.assertIn("source-scout", payload["skills"])
        validate_manifest(payload)

        payload = reviewed_payload()
        payload["skills"].append("web-crawl")
        with self.assertRaisesRegex(ManifestValidationError, "arbitrary source discovery"):
            validate_manifest(payload)

        payload = reviewed_payload()
        payload["skills"].append("install-python-package")
        with self.assertRaisesRegex(ManifestValidationError, "arbitrary source discovery"):
            validate_manifest(payload)

    def test_rejects_unknown_field_and_non_mireye_preference(self):
        payload = reviewed_payload()
        payload["fields"].append("invented_vendor_score")
        with self.assertRaisesRegex(ManifestValidationError, "reviewed catalog"):
            validate_manifest(payload)

        payload = reviewed_payload()
        payload["preferences"].append("route_duration_s")
        with self.assertRaisesRegex(ManifestValidationError, "reviewed catalog"):
            validate_manifest(payload)

    def test_rejects_source_or_code_reference_keys(self):
        for key, value in (
            ("sources", ["https://example.test"]),
            ("entrypoint", "package.module:run"),
            ("code", "import os"),
        ):
            payload = reviewed_payload()
            payload[key] = value
            with self.subTest(key=key):
                with self.assertRaisesRegex(ManifestValidationError, "unreviewed keys"):
                    validate_manifest(payload)

    def test_rejects_non_string_keys_as_validation_error(self):
        payload = reviewed_payload()
        payload[1] = "not JSON"
        with self.assertRaisesRegex(ManifestValidationError, "keys must be strings"):
            validate_manifest(payload)

    def test_rejects_missing_base_skill(self):
        payload = reviewed_payload()
        payload["skills"].remove("skeptic-review")
        with self.assertRaisesRegex(ManifestValidationError, "required reviewed"):
            validate_manifest(payload)

    def test_rejects_constraint_without_required_field(self):
        payload = reviewed_payload()
        payload["fields"] = [
            field_id
            for field_id in payload["fields"]
            if field_id not in {"fema_flood_zone", "within_floodplain_polygon"}
        ]
        payload["preferences"] = [
            field_id
            for field_id in payload["preferences"]
            if field_id in payload["fields"]
        ]
        with self.assertRaisesRegex(ManifestValidationError, "requires fema_flood_zone"):
            validate_manifest(payload)

    def test_rejects_duplicate_or_unselected_preference(self):
        payload = reviewed_payload()
        payload["skills"] = copy.copy(payload["skills"])
        payload["skills"].append(payload["skills"][0])
        with self.assertRaisesRegex(ManifestValidationError, "duplicates"):
            validate_manifest(payload)

        payload = reviewed_payload()
        payload["fields"].remove("nearest_substation_distance_m")
        with self.assertRaisesRegex(ManifestValidationError, "also be selected"):
            validate_manifest(payload)


if __name__ == "__main__":
    unittest.main()
