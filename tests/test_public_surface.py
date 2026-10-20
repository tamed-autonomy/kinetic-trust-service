"""The Service facade exposes only its approved composition contracts."""

from importlib.util import find_spec
import hashlib
from pathlib import Path
import tomllib
import unittest

import kinetic_trust_service
import kinetic_trust_service.evidence as evidence
import kinetic_trust_service.issuance as issuance


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

SERVICE_EXPORTS = {
    "EvidenceAdapter",
    "EvidenceAdapterError",
    "EvidenceHost",
    "EvidenceQuery",
    "EvaluatedWithoutProof",
    "IssuedProof",
    "IssuanceOutcome",
    "Issuer",
    "RejectedIssuance",
}

EXPECTED_SERVICE_NOTICE = """Kinetic Trust Service 1.0.0
Copyright 2026 Tamed Autonomy LLC

This independent composition library is not an official KTP SDK. It is
designed for use with Kinetic Trust Library 1.0.0, which profiles the Kinetic
Trust Protocol (KTP) v2.1.0 specification at commit
15520035267546e1035aad7beea0cc3cf9ef8f2c.
NMCITRA does not certify, maintain, or endorse this implementation. This is a
replaceable composition library, not a complete KTP deployment or application
conformance claim.

Products own sensing, source authenticity and completeness, storage, keys,
transport, failure handling, retries, human interaction, action, and
enforcement.

---

Kinetic Trust Protocol (KTP)
Copyright 2025-2026 Chris Perkins.

KTP was developed under the New Mexico Cyber Intelligence & Threat Response
Alliance (NMCITRA).

Canonical source:
https://github.com/nmcitra/ktp-rfc

Preferred attribution:
Chris Perkins, "Kinetic Trust Protocol (KTP): RFC Series,"
Version 2.1.0, September 3, 2026.
https://github.com/nmcitra/ktp-rfc

This notice identifies the provenance of the KTP specification and its
architectural terminology. It does not claim exclusive ownership of general
ideas, standard engineering concepts, or independently developed methods.

See PROVENANCE.md for the full attribution and citation norms this project
asks of downstream use:
https://github.com/nmcitra/ktp-rfc/blob/v2.1.0/PROVENANCE.md
"""


class PublicSurfaceTests(unittest.TestCase):
    def test_project_metadata_is_exact(self) -> None:
        with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as stream:
            metadata = tomllib.load(stream)
        project = metadata["project"]
        self.assertEqual(project["name"], "kinetic-trust-service")
        with self.subTest(metadata="version"):
            self.assertEqual(project["version"], "1.0.0")
        with self.subTest(metadata="dependencies"):
            self.assertEqual(
                project["dependencies"],
                ["kinetic-trust-library>=1.0.0,<1.1.0"],
            )
        self.assertEqual(project.get("optional-dependencies", {}), {})
        self.assertEqual(project["license"], "Apache-2.0")
        self.assertEqual(project.get("license-files"), ["LICENSE", "NOTICE"])
        self.assertIn(
            "Programming Language :: Python :: 3.11",
            project["classifiers"],
        )
        self.assertIn(
            "Programming Language :: Python :: 3.12",
            project["classifiers"],
        )
        self.assertIn(
            "Programming Language :: Python :: 3.13",
            project["classifiers"],
        )
        self.assertIn(
            "Programming Language :: Python :: 3.14",
            project["classifiers"],
        )

    def test_project_python_support_is_exact(self) -> None:
        with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as stream:
            project = tomllib.load(stream)["project"]
        self.assertEqual(project["requires-python"], ">=3.11")
        self.assertEqual(
            {
                item
                for item in project["classifiers"]
                if item.startswith("Programming Language :: Python :: 3.")
            },
            {
                f"Programming Language :: Python :: 3.{minor}"
                for minor in range(11, 16)
            },
        )

    def test_license_and_notice_sources_are_present_and_identify_the_service(self) -> None:
        license_path = REPOSITORY_ROOT / "LICENSE"
        notice_path = REPOSITORY_ROOT / "NOTICE"
        self.assertTrue(license_path.is_file())
        self.assertTrue(notice_path.is_file())
        license_bytes = license_path.read_bytes()
        notice_text = notice_path.read_text(encoding="utf-8")
        self.assertEqual(len(license_bytes), 11358)
        self.assertEqual(
            hashlib.sha256(license_bytes).hexdigest(),
            "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
        )
        self.assertEqual(notice_text, EXPECTED_SERVICE_NOTICE)

    def test_sdist_source_allowlist_is_exact(self) -> None:
        with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as stream:
            metadata = tomllib.load(stream)
        self.assertEqual(
            metadata["tool"]["hatch"]["build"]["targets"]["sdist"].get(
                "only-include"
            ),
            [
                "pyproject.toml",
                "README.md",
                "CONTEXT.md",
                "LICENSE",
                "NOTICE",
                "src/kinetic_trust_service",
            ],
        )

    def test_maintained_docs_publish_support_and_a_durable_context_link(self) -> None:
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        context = (REPOSITORY_ROOT / "CONTEXT.md").read_text(encoding="utf-8")
        link = (
            "https://github.com/tamed-autonomy/kinetic-trust-service/"
            "blob/main/CONTEXT.md"
        )
        self.assertIn("CPython 3.11 through 3.15", readme)
        self.assertIn("CPython 3.11 through 3.15", context)
        self.assertNotIn("3.11 through 3.14", readme)
        self.assertNotIn("3.11 through 3.14", context)
        self.assertIn(link, readme)
        self.assertNotIn("](CONTEXT.md)", readme)

    def test_root_and_focused_exports_are_exact_and_identical(self) -> None:
        self.assertEqual(set(kinetic_trust_service.__all__), SERVICE_EXPORTS)
        self.assertEqual(tuple(kinetic_trust_service.__all__), tuple(sorted(SERVICE_EXPORTS)))
        self.assertEqual(evidence.__all__, (
            "EvidenceAdapter", "EvidenceAdapterError", "EvidenceHost", "EvidenceQuery"
        ))
        self.assertEqual(issuance.__all__, [
            "EvaluatedWithoutProof", "IssuedProof", "IssuanceOutcome", "Issuer", "RejectedIssuance"
        ])
        for name in SERVICE_EXPORTS:
            owner = evidence if name.startswith("Evidence") else issuance
            self.assertIs(getattr(kinetic_trust_service, name), getattr(owner, name))
        self.assertFalse(hasattr(kinetic_trust_service, "SensorPluginHost"))
        self.assertFalse(hasattr(kinetic_trust_service, "SensorPluginError"))
        self.assertIsNone(find_spec("kinetic_trust_service.plugins"))


if __name__ == "__main__":
    unittest.main()
