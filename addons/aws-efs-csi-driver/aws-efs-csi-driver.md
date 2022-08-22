## Amazon Elastic File System - EFS
EFS file system needs to be created following the 
[respective instructions](https://docs.aws.amazon.com/efs/latest/ug/gs-step-two-create-efs-resources.html) so it can be
be mounted inside containers. To setup EFS with the MicroK8s snap you will need the File system ID of EFS. Make sure the file
system you create is accessible in the EC2 VM where the snap is running.

To test the setup after calling `sudo microk8s enable aws-efs-csi-driver -i <filesystem_id>` you can create a PVC:
```dtd
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: efs-claim
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: efs-sc
  resources:
    requests:
      storage: 5Gi
``` 
And use it in a pod:
```dtd
apiVersion: v1
kind: Pod
metadata:
  name: app1
spec:
  containers:
  - name: app1
    image: busybox
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo $(date -u) >> /data/out1.txt; sleep 5; done"]
    volumeMounts:
    - name: persistent-storage
      mountPath: /data
  volumes:
  - name: persistent-storage
    persistentVolumeClaim:
      claimName: efs-claim
```

To verify everything:
```dtd
sudo microk8s kubectl exec -ti app1 -- tail -f /data/out1.txt
``` 


# References
 - https://containerjournal.com/topics/container-networking/using-ebs-and-efs-as-persistent-volume-in-kubernetes/
 - https://github.com/kubernetes-sigs/aws-efs-csi-driver
 - https://docs.aws.amazon.com/efs/latest/ug/gs-step-two-create-efs-resources.html 