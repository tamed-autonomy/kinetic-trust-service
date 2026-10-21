"""Release automation remains immutable, tag-bound, and OIDC-only."""

from pathlib import Path
import re
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class ReleasePolicyTests(unittest.TestCase):
    def test_workflow_actions_are_approved_and_immutable(self) -> None:
        action_reference = re.compile(r"^\s*uses:\s*([^@\s]+)@([^\s#]+)")
        workflow_root = REPOSITORY_ROOT / ".github" / "workflows"
        workflow_paths = sorted(
            {*workflow_root.glob("*.yml"), *workflow_root.glob("*.yaml")}
        )

        self.assertGreaterEqual(len(workflow_paths), 3)
        found = 0
        for path in workflow_paths:
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                match = action_reference.match(line)
                if match is None:
                    continue
                found += 1
                action, revision = match.groups()
                owner = action.split("/", 1)[0]
                with self.subTest(path=path, line=line_number, action=action):
                    self.assertTrue(
                        owner in {"actions", "github"}
                        or action == "pypa/gh-action-pypi-publish"
                    )
                    self.assertRegex(revision, r"\A[0-9a-f]{40}\Z")
        self.assertGreater(found, 0)

    def test_release_workflow_is_tag_bound_and_uses_oidc(self) -> None:
        workflow = (
            REPOSITORY_ROOT / ".github" / "workflows" / "release.yml"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'on:\n  push:\n    tags:\n      - "v*"\n',
            workflow,
        )
        self.assertNotIn("workflow_dispatch:", workflow)
        self.assertNotIn("pull_request_target:", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertIn("permissions:\n  contents: read\n", workflow)
        self.assertNotIn("write-all", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertIn("github.ref_name", workflow)
        self.assertIn("github.ref_type", workflow)
        self.assertIn("          fetch-depth: 0\n", workflow)
        self.assertIn(
            "git merge-base --is-ancestor HEAD refs/remotes/origin/main",
            workflow,
        )
        self.assertIn("pyproject.toml", workflow)
        self.assertIn("tomllib", workflow)
        self.assertIn('expected_tag = f"v{project[\'version\']}"', workflow)
        self.assertIn(
            'if ref_type != "tag" or ref_name != expected_tag:',
            workflow,
        )
        self.assertIn("uses: actions/upload-artifact@", workflow)
        self.assertIn("uses: actions/download-artifact@", workflow)
        self.assertIn("uses: pypa/gh-action-pypi-publish@", workflow)
        self.assertIn("\n  publish:\n", workflow)
        build_job = workflow.split("\n  build:\n", 1)[1].split(
            "\n  publish:\n", 1
        )[0]
        self.assertNotIn("id-token: write", build_job)
        publish_job = workflow.split("\n  publish:\n", 1)[1]
        self.assertIn("    needs: build\n", publish_job)
        self.assertIn(
            "    environment:\n"
            "      name: pypi\n"
            "      url: https://pypi.org/p/kinetic-trust-service\n",
            publish_job,
        )
        self.assertIn("    permissions:\n      id-token: write\n", publish_job)
        self.assertEqual(publish_job.count("id-token: write"), 1)
        self.assertIn("      packages-dir: dist/\n", publish_job)
        self.assertNotIn("password:", publish_job)
        self.assertNotIn("secrets.", publish_job)


if __name__ == "__main__":
    unittest.main()
