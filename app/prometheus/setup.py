import os
import shutil
import tempfile

def setup_multiproc_dir() -> str:
    path = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = path
    return path