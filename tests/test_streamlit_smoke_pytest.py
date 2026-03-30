import importlib


def test_streamlit_app_imports_ok():
    # Smoke test: import the Streamlit app module to ensure it can be imported
    # in CI (we don't run the app here).
    mod = importlib.import_module("dashboard.streamlit_app")
    # Expect at least the main entrypoint or loader functions to exist
    assert hasattr(mod, "main") or hasattr(mod, "load_daily_summary")
