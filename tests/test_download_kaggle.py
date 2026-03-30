import os
import unittest
from unittest import mock


class TestDownloadKaggle(unittest.TestCase):
    @mock.patch("ingestion.download_kaggle._run_kaggle_cli")
    @mock.patch("ingestion.download_kaggle._write_kaggle_config")
    def test_download_dataset_success(self, write_cfg_mock, run_cli_mock):
        # Prepare mocks
        class Proc:
            returncode = 0
            stdout = ""
            stderr = ""

        run_cli_mock.return_value = Proc()

        # Ensure environment token is set
        with mock.patch.dict(os.environ, {"KAGGLE_API_TOKEN": "token"}):
            # Use a temporary directory inside the repo for output
            from ingestion import download_kaggle
            out_dir = os.path.join(os.path.dirname(__file__), "tmp_raw")
            # Ensure directory exists
            os.makedirs(out_dir, exist_ok=True)

            # Create a fake file to simulate download
            fpath = os.path.join(out_dir, "dataset.csv")
            with open(fpath, "w") as fh:
                fh.write("a,b\n1,2")

            # Patch _list_files to return our fake file list
            with mock.patch("ingestion.download_kaggle._list_files", return_value=["dataset.csv"]):
                files = download_kaggle.download_dataset(out_dir)
                self.assertIn("dataset.csv", files)

    @mock.patch("ingestion.download_kaggle._run_kaggle_cli")
    def test_download_dataset_cli_failure(self, run_cli_mock):
        class Proc:
            returncode = 1
            stdout = ""
            stderr = "error"

        run_cli_mock.return_value = Proc()

        with mock.patch.dict(os.environ, {"KAGGLE_API_TOKEN": "token"}):
            from ingestion import download_kaggle
            out_dir = os.path.join(os.path.dirname(__file__), "tmp_raw")
            os.makedirs(out_dir, exist_ok=True)
            with mock.patch("ingestion.download_kaggle._list_files", return_value=[]):
                with self.assertRaises(RuntimeError):
                    download_kaggle.download_dataset(out_dir)


if __name__ == "__main__":
    unittest.main()
