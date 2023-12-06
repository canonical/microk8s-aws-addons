## Amazon Elastic Load Balancer - ELB
ELB controller requires some configuration on the vpc, subnets and security groups to function properly, please check the [respective instructions](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/installation/). Please also check the [auto discovery instructions](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/subnet_discovery/).

To setup ELB with MicroK8s you'll need to determine a clusterID, which you'll use to tag subnets/security groups.

To test the setup after calling `sudo microk8s enable aws-elb-controller -c <cluster_id>` you can create a service, an ingress and a pod:
```dtd
apiVersion: v1
kind: Service
metadata:
  name: echoserver
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-scheme: internet-facing
    service.beta.kubernetes.io/aws-load-balancer-type: external
    service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: instance
spec:
  ports:
    - port: 80
      targetPort: 8080
      protocol: TCP
  type: LoadBalancer
  selector:
    app: echoserver
```

```dtd
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: echoserver
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: instance
    alb.ingress.kubernetes.io/tags: Environment=dev,Team=test
spec:
  ingressClassName: alb
  rules:
    - host: "*.amazonaws.com"
      http:
        paths:
          - path: /
            pathType: Exact
            backend:
              service:
                name: echoserver
                port:
                  number: 80
```

```dtd
apiVersion: v1
kind: Pod
metadata:
  name: echoserver
  labels:
    app: echoserver
spec:
  containers:
  - image: k8s.gcr.io/e2e-test-images/echoserver:2.5
    imagePullPolicy: Always
    name: echoserver
    ports:
    - containerPort: 8080
```

Please note that currently only the loadbalancers with `target-type: instance` are supported. IP targets need to use `amazon-vpc-cni-k8s` CNI to function, which is currently not implemented. 

# References
- https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/how-it-works/
- https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/installation/
- https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/subnet_discovery/
- https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/examples/echo_server/
