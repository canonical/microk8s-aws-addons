#!/usr/bin/bash -x

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export SCRIPT_DIR

ARCH=$(uname -m)

if ! [[ -z $AWS_ACCESS_KEY_ID || -z $AWS_SECRET_ACCESS_KEY ]];
then
  if [[ $ARCH == *"x86_64"* || $ARCH == *"aarch64"* ]];
  then
    export AWS_PAGER=""
    export AWS_REGION="${AWS_REGION:-"us-east-1"}"
    export INSTANCE_TYPE="${INSTANCE_TYPE:-"m4.large"}"

    export IMAGE_AMI_ID="/aws/service/canonical/ubuntu/server/jammy/stable/current/amd64/hvm/ebs-gp2/ami-id"
    if [[ $ARCH == *"aarch64"* ]]
    then
      export IMAGE_AMI_ID="/aws/service/canonical/ubuntu/server/jammy/stable/current/arm64/hvm/ebs-gp2/ami-id"
    fi

    K8S_USER_ARN=$(aws sts get-caller-identity --query 'Arn' --output text)
    export K8S_USER_ARN

    export SSH_KEY_PATH="${SCRIPT_DIR}/mk8s_rsa"
    rm -rf "${SSH_KEY_PATH}"
    ssh-keygen -q -f "$SSH_KEY_PATH" -t rsa -b 4096 -N ''
    PUBLIC_KEY=$(cat "${SSH_KEY_PATH}.pub")
    export PUBLIC_KEY

    export STACK_NAME="${STACK_NAME:-$(
      tr -dc A-Za-z0-9 </dev/urandom | head -c 13
      echo ''
    )}"

    aws cloudformation create-stack --stack-name "$STACK_NAME" --template-body file://"$SCRIPT_DIR"/cloudformation-template.yaml --parameters "ParameterKey=PublicKey,ParameterValue='${PUBLIC_KEY}'" "ParameterKey=K8sUserArn,ParameterValue='${K8S_USER_ARN}'" "ParameterKey=NodeInstanceType,ParameterValue='${INSTANCE_TYPE}'" "ParameterKey=LatestAmiId,ParameterValue='${IMAGE_AMI_ID}'" --tags Key=mk8s,Value=mk8s --capabilities CAPABILITY_NAMED_IAM --region $AWS_REGION
    aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME" --region "$AWS_REGION"

    NODE_IP=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey == 'NodePublicIP'].OutputValue" --output text --region "$AWS_REGION")
    export NODE_IP
    EFS_ID=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey == 'EfsId'].OutputValue" --output text --region "$AWS_REGION")
    export EFS_ID
    KUBERNETES_ADMIN_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey == 'KubernetesAdminArn'].OutputValue" --output text --region "$AWS_REGION")
    export KUBERNETES_ADMIN_ARN

    for i in $(seq 1 5); do ssh -o "StrictHostKeyChecking accept-new" -i "$SSH_KEY_PATH" ubuntu@"$NODE_IP" "lsb_release -a" && s=0 && break || s=$? && sleep 15; done; (exit "$s")

    ssh -o "StrictHostKeyChecking accept-new" -i "$SSH_KEY_PATH" ubuntu@"$NODE_IP" "
      sudo echo CLUSTER_ID=mk8s | sudo tee -a /etc/environment > /dev/null
      sudo echo AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} | sudo tee -a /etc/environment > /dev/null
      sudo echo AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} | sudo tee -a /etc/environment > /dev/null
      sudo echo KUBERNETES_ADMIN_ARN=${KUBERNETES_ADMIN_ARN} | sudo tee -a /etc/environment > /dev/null
      sudo echo EFS_ID=${EFS_ID} | sudo tee -a /etc/environment > /dev/null
    "

    if [[ ${TO_CHANNEL} =~ /.*/microk8s.*snap ]]; then
      scp -o "StrictHostKeyChecking accept-new" -i "$SSH_KEY_PATH" "${TO_CHANNEL}" ubuntu@"$NODE_IP":"microk8s.snap"
      ssh -o "StrictHostKeyChecking accept-new" -i "$SSH_KEY_PATH" ubuntu@"$NODE_IP" "
        sudo snap install ~/microk8s.snap --dangerous --classic
      "
    else
      ssh -o "StrictHostKeyChecking accept-new" -i "$SSH_KEY_PATH" ubuntu@"$NODE_IP" "
        sudo snap install microk8s --channel=${TO_CHANNEL} --classic
      "
    fi

    ssh -o "StrictHostKeyChecking accept-new" -i "$SSH_KEY_PATH" ubuntu@"$NODE_IP" "
      sudo microk8s status --wait
      sudo python3 -m pytest -s /var/snap/microk8s/common/addons/eksd/tests/test-addons.py
    "

    aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$AWS_REGION"
  fi
fi
