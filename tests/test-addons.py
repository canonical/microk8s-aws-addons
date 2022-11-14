import pytest
import os
from pathlib import Path

from utils import (
    get_efs_id,
    is_ec2_instance,
    microk8s_enable,
    microk8s_disable,
    microk8s_reset,
    get_aws_access_key_id,
    get_aws_secret_access_key,
    get_efs_id,
    get_cluster_id,
)

from validators import (
    validate_aws_iam_authenticator,
    validate_aws_ebs_csi_driver,
    validate_aws_efs_csi_driver,
    validate_aws_elb_controller,
)

TEMPLATES = Path(__file__).absolute().parent / "templates"


class TestAddons(object):
    @pytest.fixture(scope="session", autouse=True)
    def clean_up(self):
        """
        Clean up after a test
        """
        yield
        microk8s_reset()

    @pytest.mark.skipif(
        is_ec2_instance() == False,
        reason="Skipping iam tests since we are not in an EC2 instance",
    )
    @pytest.mark.skipif(
        "AWS_ACCESS_KEY_ID" not in os.environ,
        reason="Skipping iam tests since aws access key id is not provided",
    )
    @pytest.mark.skipif(
        "AWS_SECRET_ACCESS_KEY" not in os.environ,
        reason="Skipping iam tests since aws access key secret is not provided",
    )
    @pytest.mark.skipif(
        "KUBERNETES_ADMIN_ARN" not in os.environ,
        reason="Skipping iam tests since admin arn is not provided",
    )
    def test_aws_iam_authenticator(self):
        print("Enabling aws-iam-authenticator")
        microk8s_enable("aws-iam-authenticator")
        print("Validating aws-iam-authenticator")
        validate_aws_iam_authenticator()
        print("Disabling aws-iam-authenticator")
        microk8s_disable("aws-iam-authenticator")

    @pytest.mark.skipif(
        is_ec2_instance() == False,
        reason="Skipping ebs tests since we are not in an EC2 instance",
    )
    @pytest.mark.skipif(
        "AWS_ACCESS_KEY_ID" not in os.environ,
        reason="Skipping ebs tests since aws access key id is not provided",
    )
    @pytest.mark.skipif(
        "AWS_SECRET_ACCESS_KEY" not in os.environ,
        reason="Skipping ebs tests since aws access key secret is not provided",
    )
    @pytest.mark.skipif(
        os.environ.get("STRICT") == "yes",
        reason="Skipping ebs tests in strict confinement as they are expected to fail",
    )
    def test_aws_ebs_csi_driver(self):
        print("Enabling aws-ebs-csi-driver")
        microk8s_enable(
            "aws-ebs-csi-driver -k {} -a {}".format(
                get_aws_access_key_id(), get_aws_secret_access_key()
            )
        )
        print("Validating aws-ebs-csi-driver")
        validate_aws_ebs_csi_driver()
        print("Disabling aws-ebs-csi-driver")
        microk8s_disable("aws-ebs-csi-driver")

    @pytest.mark.skipif(
        is_ec2_instance() == False,
        reason="Skipping efs tests since we are not in an EC2 instance",
    )
    @pytest.mark.skipif(
        "AWS_ACCESS_KEY_ID" not in os.environ,
        reason="Skipping efs tests since aws access key id is not provided",
    )
    @pytest.mark.skipif(
        "AWS_SECRET_ACCESS_KEY" not in os.environ,
        reason="Skipping efs tests since aws access key secret is not provided",
    )
    @pytest.mark.skipif(
        "EFS_ID" not in os.environ,
        reason="Skipping efs tests since efs id is not provided",
    )
    @pytest.mark.skipif(
        os.environ.get("STRICT") == "yes",
        reason="Skipping efs tests in strict confinement as they are expected to fail",
    )
    def test_aws_efs_csi_driver(self):
        print("Enabling aws-efs-csi-driver")
        microk8s_enable("aws-efs-csi-driver -i {}".format(get_efs_id()))
        print("Validating aws-efs-csi-driver")
        validate_aws_efs_csi_driver()
        print("Disabling aws-efs-csi-driver")
        microk8s_disable("aws-efs-csi-driver")

    @pytest.mark.skipif(
        is_ec2_instance() == False,
        reason="Skipping elb tests since we are not in an EC2 instance",
    )
    @pytest.mark.skipif(
        "AWS_ACCESS_KEY_ID" not in os.environ,
        reason="Skipping elb tests since aws access key id is not provided",
    )
    @pytest.mark.skipif(
        "AWS_SECRET_ACCESS_KEY" not in os.environ,
        reason="Skipping elb tests since aws access key secret is not provided",
    )
    @pytest.mark.skipif(
        "CLUSTER_ID" not in os.environ,
        reason="Skipping elb tests since cluster id is not provided",
    )
    @pytest.mark.skipif(
        os.environ.get("STRICT") == "yes",
        reason="Skipping elb tests in strict confinement as they are expected to fail",
    )
    def test_aws_elb_controller(self):
        print("Enabling aws-elb-controller")
        microk8s_enable("aws-elb-controller -c {}".format(get_cluster_id()))
        print("Validating aws-elb-controller")
        validate_aws_elb_controller()
        print("Disabling aws-elb-controller")
        microk8s_disable("aws-elb-controller")