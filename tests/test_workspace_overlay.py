"""Integrity regressions for committed code over an immutable artifact snapshot."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_workspace_overlay import REQUIRED, verify


class WorkspaceOverlayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Integrity test")
        self.git("config", "user.email", "test@example.invalid")
        (self.root / ".gitignore").write_text("handoff/\npreserved.bin\n")
        for name in REQUIRED:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"original\n")
        (self.root / "preserved.bin").write_bytes(b"evidence")
        self.git("add", ".")
        self.git("commit", "-qm", "Original payload")
        names = [*REQUIRED, "preserved.bin"]
        manifest = {"schema_version": 1, "base_commit": self.git("rev-parse", "HEAD").strip(),
                    "files": {n: {"bytes": (self.root / n).stat().st_size,
                                   "sha256": hashlib.sha256((self.root / n).read_bytes()).hexdigest()}
                              for n in names}}
        p = self.root / "handoff/manifest.json"
        p.parent.mkdir()
        p.write_text(json.dumps(manifest))
        self.digest = hashlib.sha256(p.read_bytes()).hexdigest()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.DEVNULL).decode()

    def test_committed_document_update_preserves_artifact_checks(self):
        (self.root / "START_HERE.md").write_text("Documented new navigation\n")
        (self.root / "new-report.md").write_text("New report\n")
        self.git("add", ".")
        self.git("commit", "-qm", "Small code and documentation update")
        result = verify(self.root, self.digest)
        self.assertEqual(result["intentional_committed_overlays"], ["START_HERE.md"])
        self.assertIn("new-report.md", result["new_tracked_files"])

    def test_same_size_ignored_corruption_is_rejected(self):
        (self.root / "preserved.bin").write_bytes(b"damaged!")
        with self.assertRaisesRegex(ValueError, "Unexplained payload change"):
            verify(self.root, self.digest)

    def test_manifest_rewrite_is_rejected(self):
        (self.root / "handoff/manifest.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "independently pinned"):
            verify(self.root, self.digest)

    def test_uncommitted_update_is_rejected(self):
        (self.root / "START_HERE.md").write_text("Uncommitted\n")
        with self.assertRaisesRegex(ValueError, "working changes"):
            verify(self.root, self.digest)

    def test_committed_payload_deletion_is_rejected(self):
        self.git("rm", "START_HERE.md")
        self.git("commit", "-qm", "Delete payload")
        with self.assertRaisesRegex(ValueError, "Missing"):
            verify(self.root, self.digest)

    def test_ignored_payload_symlink_is_rejected(self):
        (self.root / "preserved.bin").unlink()
        (self.root / "preserved.bin").symlink_to("START_HERE.md")
        with self.assertRaisesRegex(ValueError, "symlinked"):
            verify(self.root, self.digest)

    def test_cached_clean_index_cannot_hide_overlay_corruption(self):
        p = self.root / "START_HERE.md"
        p.write_text("committed overlay\n")
        self.git("add", "START_HERE.md")
        self.git("commit", "-qm", "Overlay")
        self.git("update-index", "--assume-unchanged", "START_HERE.md")
        p.write_text("corrupted overlay\n")
        self.assertEqual(self.git("status", "--porcelain"), "")
        with self.assertRaisesRegex(ValueError, "committed blob"):
            verify(self.root, self.digest)


if __name__ == "__main__":
    unittest.main()
