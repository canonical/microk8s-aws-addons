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

    def test_invalid_addon(self):
        with pytest.raises(sh.ErrorReturnCode_1):
            sh.microk8s.enable.foo()

    def test_help_text(self):
        status = yaml.safe_load(sh.microk8s.status(format="yaml").stdout)
        expected = {a["name"]: "disabled" for a in status["addons"]}
        expected["ha-cluster"] = "enabled"
        expected["helm"] = "enabled"
        expected["helm3"] = "enabled"

        assert expected == {a["name"]: a["status"] for a in status["addons"]}

        for addon in status["addons"]:
            sh.microk8s.enable(addon["name"], "--", "--help")

        assert expected == {a["name"]: a["status"] for a in status["addons"]}

        for addon in status["addons"]:
            sh.microk8s.disable(addon["name"], "--", "--help")

        assert expected == {a["name"]: a["status"] for a in status["addons"]}
