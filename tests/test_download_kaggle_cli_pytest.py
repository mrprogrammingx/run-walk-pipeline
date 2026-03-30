import os
import subprocess
import sys
from unittest import mock


def test_download_kaggle_main_returns_nonzero_when_no_token(monkeypatch, tmp_path):
    # Ensure KAGGLE_API_TOKEN is not set
    monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)

    # Run the module as a subprocess using the current interpreter
    cmd = [sys.executable, "-m", "ingestion.download_kaggle"]
    env = os.environ.copy()
    env.pop("KAGGLE_API_TOKEN", None)
    # run from an isolated temporary working directory so imports don't pick up repo-local state
    proc = subprocess.run(cmd, cwd=str(tmp_path), env=env)
    # main() should exit with non-zero when token missing
    assert proc.returncode != 0


def test_download_kaggle_main_success(monkeypatch, tmp_path):
    # Simulate successful download by patching download_dataset
    import ingestion.download_kaggle as mod

    def fake_download(output_dir, dataset=mod.DATASET):
        # create a fake file
        os.makedirs(output_dir, exist_ok=True)
        p = os.path.join(output_dir, "fake.csv")
        with open(p, "w") as fh:
            fh.write("a,b\n1,2")
        return ["fake.csv"]

    monkeypatch.setenv("KAGGLE_API_TOKEN", "token")
    monkeypatch.setattr(mod, "download_dataset", fake_download)

    # Call main() directly and assert it returns 0
    ret = mod.main()
    assert ret == 0
