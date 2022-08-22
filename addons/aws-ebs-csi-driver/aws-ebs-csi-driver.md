## Amazon Elastic Block Store - EBS
The driver requires IAM permission to manage Amazon EBS volumes on user's behalf. An IAM user with proper permissions
needs to be provided during `sudo microk8s enable aws-ebs-csi-driver`. You will be asked for the user's key ID and access ID.

To test the setup after calling `sudo microk8s enable aws-ebs-csi-driver -k <iam_user_key_id> -a <iam_user_access_key>` you can create a PVC:
```dtd
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ebs-claim
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ebs-sc
  resources:
    requests:
      storage: 4Gi
``` 
And use it in a pod:
```dtd
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: centos
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo $(date -u) >> /data/out.txt; sleep 5; done"]
    volumeMounts:
    - name: persistent-storage
      mountPath: /data
  volumes:
  - name: persistent-storage
    persistentVolumeClaim:
      claimName: ebs-claim
```

To verify everything:
```dtd
sudo microk8s kubectl exec -ti app -- tail -f /data/out.txt
``` 

# References
 - https://containerjournal.com/topics/container-networking/using-ebs-and-efs-as-persistent-volume-in-kubernetes/
 - https://github.com/kubernetes-sigs/aws-ebs-csi-driver