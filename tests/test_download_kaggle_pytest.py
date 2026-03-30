import os
import shutil
import pytest


@pytest.fixture()
def tmp_out(tmp_path):
    d = tmp_path / "raw"
    d.mkdir()
    return str(d)


def test_download_dataset_success(monkeypatch, tmp_out):
    # Mock _run_kaggle_cli and _write_kaggle_config
    from ingestion import download_kaggle

    class Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setenv("KAGGLE_API_TOKEN", "token")
    monkeypatch.setattr(download_kaggle, "_run_kaggle_cli", lambda out, ds: Proc())
    monkeypatch.setattr(download_kaggle, "_write_kaggle_config", lambda u, k: None)
    monkeypatch.setattr(download_kaggle, "_list_files", lambda p: ["dataset.csv"])

    files = download_kaggle.download_dataset(tmp_out)
    assert "dataset.csv" in files


def test_download_dataset_cli_failure(monkeypatch, tmp_out):
    from ingestion import download_kaggle

    class Proc:
        returncode = 1
        stdout = ""
        stderr = "error"

    monkeypatch.setenv("KAGGLE_API_TOKEN", "token")
    monkeypatch.setattr(download_kaggle, "_run_kaggle_cli", lambda out, ds: Proc())
    monkeypatch.setattr(download_kaggle, "_list_files", lambda p: [])

    with pytest.raises(RuntimeError):
        download_kaggle.download_dataset(tmp_out)
