import importlib.util
import os
import sys
import types


def test_airflow_dag_creates_tasks_and_dependencies(tmp_path, monkeypatch):
    # Create minimal stubs for airflow to allow importing the DAG file
    created_ops = []
    dependencies = []

    class FakeDAG:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakePythonOperator:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.task_id = kwargs.get("task_id")
            created_ops.append(self)

        def __rshift__(self, other):
            # support chaining like op1 >> op2
            dependencies.append((self.task_id, getattr(other, "task_id", None)))
            return other

    # Insert fake modules into sys.modules so `from airflow import DAG` and
    # `from airflow.operators.python import PythonOperator` work.
    fake_airflow = types.ModuleType("airflow")
    fake_airflow.DAG = FakeDAG

    fake_ops = types.ModuleType("airflow.operators")
    fake_python_pkg = types.ModuleType("airflow.operators.python")
    fake_python_pkg.PythonOperator = FakePythonOperator

    monkeypatch.setitem(sys.modules, "airflow", fake_airflow)
    monkeypatch.setitem(sys.modules, "airflow.operators", fake_ops)
    monkeypatch.setitem(sys.modules, "airflow.operators.python", fake_python_pkg)

    # Load the DAG module by path (avoids package import issues)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dag_path = os.path.join(repo_root, "airflow", "dag.py")
    spec = importlib.util.spec_from_file_location("tests.airflow_dag", dag_path)
    module = importlib.util.module_from_spec(spec)
    # Execute the module (this will instantiate operators using FakePythonOperator)
    spec.loader.exec_module(module)

    # Expect three operators created: download, ingest, transform
    task_ids = [op.task_id for op in created_ops]
    assert "download" in task_ids
    assert "ingest" in task_ids
    assert "transform" in task_ids

    # Expect dependencies chain (download -> ingest -> transform) recorded
    assert ("download", "ingest") in dependencies or ("download", None) in dependencies
    assert ("ingest", "transform") in dependencies or ("ingest", None) in dependencies
