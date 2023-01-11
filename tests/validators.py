import os
import yaml
import time
from subprocess import check_call
from pathlib import Path

from utils import (
    kubectl,
    wait_for_pod_state,
    kubectl_get,
    run_until_success,
    get_kubernetes_admin_arn,
)

TEMPLATES = Path(__file__).absolute().parent / "templates"


def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def validate_aws_iam_authenticator():
    yaml.add_representer(str, str_presenter)
    yaml.representer.SafeRepresenter.add_representer(str, str_presenter)

    kubectl(
        "annotate cm aws-iam-authenticator -n kube-system kubectl.kubernetes.io/last-applied-configuration-"
    )
    config_map = kubectl_get("cm aws-iam-authenticator -n kube-system")
    current_iam_config = yaml.safe_load(config_map["data"]["config.yaml"])
    cluster_id = current_iam_config["clusterID"]

    template_iam_config = TEMPLATES / "template-iam-config.yaml"
    updated_cm_manifest = "/tmp/updated-iam-cm.yaml"
    with open(updated_cm_manifest, "w+") as cmf:
        with open(template_iam_config, "r") as icf:
            iam_config = yaml.safe_load(icf)
            iam_config["clusterID"] = cluster_id
            iam_config["server"]["mapRoles"][0]["roleARN"] = get_kubernetes_admin_arn()
            config_map["data"]["config.yaml"] = yaml.safe_dump(iam_config)
            cmf.write(yaml.safe_dump(config_map))

    kubectl("apply -n kube-system -f {}".format(updated_cm_manifest))
    kubectl("rollout restart ds aws-iam-authenticator -n kube-system")
    kubectl("rollout status ds aws-iam-authenticator -n kube-system --timeout=180s")

    kube_config = yaml.safe_load(run_until_success("/snap/bin/microk8s.config"))

    template_kubeconfig_file = TEMPLATES / "template-kube-config.yaml"
    tmp_kubeconfig = "/tmp/iam-kube-config"
    with open(tmp_kubeconfig, "w+") as kcf:
        with open(template_kubeconfig_file, "r") as tkf:
            template_kubeconfig = yaml.safe_load(tkf)
            template_kubeconfig["clusters"][0]["cluster"]["server"] = kube_config[
                "clusters"
            ][0]["cluster"]["server"]
            template_kubeconfig["clusters"][0]["cluster"][
                "certificate-authority-data"
            ] = kube_config["clusters"][0]["cluster"]["certificate-authority-data"]
            template_kubeconfig["users"][0]["user"]["exec"]["args"][2] = cluster_id
            template_kubeconfig["users"][0]["user"]["exec"]["args"][
                4
            ] = get_kubernetes_admin_arn()
            kcf.write(yaml.safe_dump(template_kubeconfig))

    check_call(
        "/snap/bin/kubectl get all -A".split(),
        env={**os.environ, "KUBECONFIG": tmp_kubeconfig},
    )


def validate_aws_ebs_csi_driver():
    pvc_manifest = TEMPLATES / "ebs-pvc.yaml"
    pod_manifest = TEMPLATES / "ebs-pod.yaml"
    kubectl("apply -f {}".format(pvc_manifest))
    kubectl("apply -f {}".format(pod_manifest))
    wait_for_pod_state("ebs-pod", "default", "running")
    output = kubectl("exec ebs-pod -- ls /data", timeout_insec=900, err_out="no")
    assert "out.txt" in output
    kubectl("delete pod ebs-pod")
    kubectl("delete pvc ebs-claim")


def validate_aws_efs_csi_driver():
    pvc_manifest = TEMPLATES / "efs-pvc.yaml"
    pod_manifest = TEMPLATES / "efs-pod.yaml"
    kubectl("apply -f {}".format(pvc_manifest))
    kubectl("apply -f {}".format(pod_manifest))
    wait_for_pod_state("efs-pod", "default", "running")
    output = kubectl("exec efs-pod -- ls /data", timeout_insec=900, err_out="no")
    assert "out.txt" in output
    kubectl("delete pod efs-pod")
    kubectl("delete pvc efs-claim")


def validate_aws_elb_controller():
    pod_manifest = TEMPLATES / "elb-pod.yaml"
    service_manifest = TEMPLATES / "elb-service.yaml"
    ingress_manifest = TEMPLATES / "elb-ingress.yaml"
    kubectl("apply -f {}".format(pod_manifest))
    wait_for_pod_state("echoserver", "echoserver", "running")
    kubectl("apply -f {}".format(service_manifest))
    kubectl("apply -f {}".format(ingress_manifest))
    time.sleep(15)
    svc = kubectl_get("svc echoserver -n echoserver")
    assert "ingress" in svc["status"]["loadBalancer"]
    assert len(svc["status"]["loadBalancer"]["ingress"][0]["hostname"]) > 0
    ing = kubectl_get("ingress echoserver -n echoserver")
    assert "ingress" in ing["status"]["loadBalancer"]
    assert len(ing["status"]["loadBalancer"]["ingress"][0]["hostname"]) > 0
    kubectl("delete ing echoserver -n echoserver")
    kubectl("delete pod echoserver -n echoserver")
    kubectl("delete svc echoserver -n echoserver")
