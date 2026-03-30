import shutil
import subprocess
import sys
import os
import pytest


def test_make_ci_dry_run_prints_expected_steps():
    """Do a dry-run of `make ci` and ensure the printed commands include the
    sample-parquet python block invocation and the pytest command. Skip if
    `make` is not available on PATH.
    """
    if shutil.which("make") is None:
        pytest.skip("make not available on PATH")

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Use `make -n ci` to print the commands without executing them.
    proc = subprocess.run(["make", "-n", "ci"], cwd=repo_root, capture_output=True, text=True)
    assert proc.returncode == 0

    out = proc.stdout + proc.stderr

    # The makefile's ci target now calls the helper script and then runs pytest.
    assert "python scripts/create_sample_parquet.py" in out
    assert "python -m pytest" in out
