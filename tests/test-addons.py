import pytest
import os
import platform
import sh
import yaml
from pathlib import Path

from utils import (
    microk8s_reset,
)
from subprocess import CalledProcessError, check_call

TEMPLATES = Path(__file__).absolute().parent / "templates"


class TestAddons(object):
    @pytest.fixture(scope="session", autouse=True)
    def clean_up(self):
        """
        Clean up after a test
        """
        yield
        microk8s_reset()
