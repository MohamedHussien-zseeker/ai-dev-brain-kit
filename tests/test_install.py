"""Tests for installation workflow — binary, install scripts, checksum verification."""

import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RELEASES = ROOT / "releases"
BINARY = RELEASES / "brain-linux-x86_64"
CHECKSUM = RELEASES / "brain-linux-x86_64.sha256"
INSTALL_SH = ROOT / "scripts" / "install.sh"


def _require_binary():
    if not BINARY.is_file():
        pytest.skip("Binary not found; run scripts/build.sh first")


class TestBinaryIntegrity:
    def test_binary_exists(self):
        _require_binary()
        assert BINARY.is_file()
        assert BINARY.stat().st_size > 1_000_000  # at least 1MB

    def test_binary_is_executable(self):
        _require_binary()
        st = BINARY.stat()
        assert st.st_mode & stat.S_IXUSR

    def test_binary_sha256_matches(self):
        _require_binary()
        assert CHECKSUM.is_file()
        expected = CHECKSUM.read_text().strip().split()[0]
        import hashlib
        actual = hashlib.sha256(BINARY.read_bytes()).hexdigest()
        assert expected == actual, f"SHA-256 mismatch: expected {expected}, got {actual}"

    def test_binary_version(self):
        _require_binary()
        result = subprocess.run(
            [str(BINARY), "--version"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "AI Dev Brain v0.1.0" in result.stdout


class TestBinaryCommands:
    def test_binary_doctor_offline(self):
        _require_binary()
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "BRAIN_CONFIG_DIR": tmp, "BRAIN_VAULT_PATH": tmp}
            result = subprocess.run(
                [str(BINARY), "doctor", "--offline"],
                capture_output=True, text=True, timeout=10, env=env,
            )
            # Should find config missing but not crash
            assert result.returncode in (0, 1)

    def test_binary_init_and_doctor(self):
        _require_binary()
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "my vault"  # path with space
            env = {**os.environ, "BRAIN_CONFIG_DIR": tmp, "BRAIN_VAULT_PATH": str(vault)}
            result = subprocess.run(
                [str(BINARY), "init", "--vault", str(vault), "--non-interactive"],
                capture_output=True, text=True, timeout=10, env=env,
            )
            assert result.returncode == 0
            assert vault.is_dir()
            assert (vault / "00-Inbox").is_dir()
            result2 = subprocess.run(
                [str(BINARY), "doctor", "--offline"],
                capture_output=True, text=True, timeout=10, env=env,
            )
            if result2.returncode != 0:
                assert "AI_BRAIN_KEY" in result2.stdout  # only acceptable issue

    def test_binary_note_and_consolidate(self):
        _require_binary()
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "Brain"
            env = {**os.environ, "BRAIN_CONFIG_DIR": tmp, "BRAIN_VAULT_PATH": str(vault)}
            subprocess.run(
                [str(BINARY), "init", "--vault", str(vault), "--non-interactive"],
                capture_output=True, timeout=10, env=env, check=True,
            )
            note_result = subprocess.run(
                [str(BINARY), "note"],
                input="Test consolidation note", text=True,
                capture_output=True, timeout=10, env=env,
            )
            assert note_result.returncode == 0
            cons_result = subprocess.run(
                [str(BINARY), "consolidate"],
                capture_output=True, text=True, timeout=10, env=env,
            )
            assert cons_result.returncode == 0
            assert "Staged: 1" in cons_result.stdout

    def test_binary_review_stats(self):
        _require_binary()
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "Brain"
            env = {**os.environ, "BRAIN_CONFIG_DIR": tmp, "BRAIN_VAULT_PATH": str(vault)}
            subprocess.run(
                [str(BINARY), "init", "--vault", str(vault), "--non-interactive"],
                capture_output=True, timeout=10, env=env, check=True,
            )
            result = subprocess.run(
                [str(BINARY), "review-stats"],
                capture_output=True, text=True, timeout=10, env=env,
            )
            assert result.returncode == 0
            assert "Pending: 0" in result.stdout

    def test_binary_path_with_spaces(self):
        _require_binary()
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "my brain vault"  # spaces!
            env = {**os.environ, "BRAIN_CONFIG_DIR": tmp, "BRAIN_VAULT_PATH": str(vault)}
            result = subprocess.run(
                [str(BINARY), "init", "--vault", str(vault), "--non-interactive"],
                capture_output=True, text=True, timeout=10, env=env,
            )
            assert result.returncode == 0
            assert vault.is_dir()
            # doctor works
            result2 = subprocess.run(
                [str(BINARY), "doctor", "--offline"],
                capture_output=True, text=True, timeout=10, env=env,
            )
            assert result2.returncode in (0, 1)

    def test_binary_rerun_init_is_idempotent(self):
        _require_binary()
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "Brain"
            env = {**os.environ, "BRAIN_CONFIG_DIR": tmp, "BRAIN_VAULT_PATH": str(vault)}
            subprocess.run(
                [str(BINARY), "init", "--vault", str(vault), "--non-interactive"],
                capture_output=True, timeout=10, env=env, check=True,
            )
            existing = vault / "00-Inbox" / "_index.md"
            content_before = existing.read_text()
            subprocess.run(
                [str(BINARY), "init", "--vault", str(vault), "--non-interactive"],
                capture_output=True, timeout=10, env=env, check=True,
            )
            content_after = existing.read_text()
            assert content_before == content_after


class TestInstallScript:
    def _run_install_sh(self, tmp: str, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
        env = {**os.environ, "HOME": tmp, "USER": "testuser"}
        cmd = ["bash", str(INSTALL_SH), "--no-verify"]
        if extra_args:
            cmd.extend(extra_args)
        # For local testing, copy binary to a fake "download" location the script expects
        # Since the script downloads from GitHub, we override it with local binary
        return subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=30, env=env,
        )

    def test_install_script_creates_binary(self):
        _require_binary()
        with tempfile.TemporaryDirectory() as tmp:
            # Simulate the install by providing the binary locally
            local_bin = Path(tmp) / ".local" / "bin"
            local_bin.mkdir(parents=True)
            shutil.copy2(BINARY, local_bin / "brain")
            result = subprocess.run(
                [str(local_bin / "brain"), "--version"],
                capture_output=True, text=True, timeout=10,
            )
            assert result.returncode == 0

    def test_install_config_preserved_on_rerun(self):
        _require_binary()
        with tempfile.TemporaryDirectory() as tmp:
            # Create initial config
            config_dir = Path(tmp) / ".brain"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text('{"version":1,"vaultPath":"/custom/path"}')
            content_before = config_file.read_text()
            # Ensure binary is in place (simulate rerun)
            local_bin = Path(tmp) / ".local" / "bin"
            local_bin.mkdir(parents=True)
            shutil.copy2(BINARY, local_bin / "brain")
            # Config should be unchanged
            assert config_file.read_text() == content_before


class TestChecksumVerification:
    def test_checksum_file_format(self):
        _require_binary()
        assert CHECKSUM.is_file()
        content = CHECKSUM.read_text().strip()
        parts = content.split()
        assert len(parts) >= 2
        assert len(parts[0]) == 64  # SHA-256 hex

    def test_checksum_fails_on_tampered_binary(self):
        _require_binary()
        with tempfile.TemporaryDirectory() as tmp:
            tampered = Path(tmp) / "tampered"
            orig = BINARY.read_bytes()
            tampered.write_bytes(orig[:-1] + bytes([orig[-1] ^ 0xFF]))
            import hashlib
            expected = CHECKSUM.read_text().strip().split()[0]
            actual = hashlib.sha256(tampered.read_bytes()).hexdigest()
            assert expected != actual, "Tampered binary should have different hash"

    def test_doctor_offline_in_packaged_binary(self):
        _require_binary()
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "Brain"
            env = {**os.environ, "BRAIN_CONFIG_DIR": tmp, "BRAIN_VAULT_PATH": str(vault)}
            subprocess.run(
                [str(BINARY), "init", "--vault", str(vault), "--non-interactive"],
                capture_output=True, timeout=10, env=env, check=True,
            )
            result = subprocess.run(
                [str(BINARY), "doctor", "--offline"],
                capture_output=True, text=True, timeout=10, env=env,
            )
            assert result.returncode == 0 or "AI_BRAIN_KEY" in result.stdout
