import shutil

import pytest

from ma_deallab.ingestion import default_data_dir, load_case
from ma_deallab.services import build_run


@pytest.fixture
def case():
    return load_case()


@pytest.fixture(scope="session")
def run():
    return build_run()


@pytest.fixture
def data_dir(tmp_path):
    target = tmp_path / "fixtures"
    shutil.copytree(default_data_dir(), target)
    return target
