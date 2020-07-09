# Create production-grade EKS cluster

### Code Description:
1. modules - reusable terraform code
1. live    - contains code for different environment

### Prequisite
1. Install Terraform
2. AWS Account
3. Configure AWS with "aws configure"

### Clone the repository

```
(base)$ git clone -b feat/terraform https://github.com/tigerrepository/MLE-Playground.git
(base)$ cd MLE-Playground/terraform/eks
```

### Initialize terraform to store state in backend
It is recommended to have terraform state files in remote backend to avoid issues like manual errors, locking and secrets. Remote backends allow you to store the state file in a remote, shared store. We have used S3 to store the terraform state files by enabling encryption and accidental delete. It is highly recommended that you enable Bucket Versioning on the S3 bucket to allow for state recovery in the case of accidental deletions and human error.

It is also recommended to isolate the state files at environment and component level like we do in this example

To run terraform apply, Terraform will automatically acquire a lock; if someone else is already running apply, they will already have the lock, and you will have to wait

Create S3 bucket and dynamo db to lock the state during the changes
```
(base)$ cd live/staging/global
(base)$ terraform init
(base)$ terraform plan
(base)$ terraform apply
```

Above commands creates the S3 bucket and dynamodb

Note: Above step is one time

### Create IAM roles:

Check the plan that it includes all resource in terraform script
```
(base)$ cd live/staging/iam
(base)$ terraform init
(base)$ terraform plan
```
Once reviewed, run apply command
```
(base)$ terraform apply
```

### Create VPC

Check the plan that it includes all resource in terraform script
```
(base)$ cd live/staging/vpc
(base)$ terraform init
(base)$ terraform plan
```

```
(base)$ terraform apply
```
Once review the plan and apply. Double check and type "yes"

Above comand creates the vpc, subnets, internet gateway, route tables and its output will be stored in variables as in output.tf. Moreover, tf state will be stored in **staging/eks/vpc/terraform.tfstate** with outputs. We do this since we need output of vpc like vpc_id and subnet_id while creating other AWS services that resides inside vpc. For instance, eks cluster and worker nodes.

### Create EKS Cluster
Now we need to create eks cluster inside the private subnet of vpc that we created above. The control plane of EKS will be in private subnet to prevent outside access. Only services inside vpc will have access to each other.

Check the plan that it includes all resource in terraform script
```
(base)$ cd live/staging/services/cluster
(base)$ terraform init
(base)$ terraform plan
```

```
(base)$ terraform apply
```
Once review the plan and apply. Double check and type "yes"

Above comand creates the eks cluster and its output will be stored in variables as in output.tf. Moreover, tf state will be stored in **"staging/eks/services/eks/terraform.tfstate** with outputs. We do this since we need output of instance like instance_id and avaliablility zone while creating and attaching ebs volume instance that we do in next step.

### Create RDS Postgres instance
We will create persistence tier inside the private subnet of the vpc that we created in the previous step. For persistence, we use RDS postgres instance.

Check the plan that it includes all resource in terraform script
```
(base)$ cd live/staging/persistence
(base)$ terraform init
(base)$ terraform plan
```

```
(base)$ terraform apply
```
Once review the plan and apply. Double check and type "yes"

Above comand creates the ebs volume. Moreover, tf state will be stored in **staging/eks/persistence/terraform.tfstate**


### Create EFS storage for persistent volume
Stateful pod uses persistent volume to save its state permanently. We need to create EFS for saving state.

Check the plan that it includes all resource in terraform script
```
(base)$ cd live/staging/storage/efs
(base)$ terraform init
(base)$ terraform plan
```

```
(base)$ terraform apply
```

### Create kuberenetes service account to access AWS services without credentials management
We use service account to access AWS services. This get rid of credentials maintainence. First create the namespace where you want to create service account

Check the plan that it includes all resource in terraform script
```
(base)$ cd live/staging/services/namespace
(base)$ terraform init
(base)$ terraform plan
```

```
(base)$ terraform apply
```
```
(base)$ cd live/staging/services/sa
(base)$ terraform init
(base)$ terraform plan
```

```
(base)$ terraform apply
```

Above command creates namespace and service account under that namespace


### Create managed nodegroup
Amazon EKS managed node groups automate the provisioning and lifecycle management of nodes (Amazon EC2 instances) for Amazon EKS Kubernetes clusters. With Amazon EKS managed node groups, you don’t need to separately provision or register the Amazon EC2 instances that provide compute capacity to run your Kubernetes applications. You can create, update, or terminate nodes for your cluster with a single operation.

```
(base)$ cd live/staging/services/nodegroup
(base)$ terraform init
(base)$ terraform plan
```

```
(base)$ terraform apply
```

### Create un-managed nodegroup
We create unmanaged nodegroup for mixed instance policy wherein we create spot instance and ondemand instance in the same nodegroup. Also, we need to register the instance with eks cluster for unmanaged nodegroup

```
(base)$ cd live/staging/services/workers
(base)$ terraform init
(base)$ terraform plan
```

```
(base)$ terraform apply
```

Once un-managed nodegroup created, we need to allow access from worker node to eks cluster. To do that we need to create k8s config map. For instance,

apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    - rolearn: arn:aws:iam::171774164293:role/tiger-mle-worker-role  # worker node iam role
      username: system:node:{{EC2PrivateDNSName}}
      groups:
        - system:bootstrappers
        - system:nodes

```
(base)$ kubectl apply -f aws-auth-cm.yaml
```

To validate the node gets added, run the below command

```
(base)$ kubectl get nodes
```

### Gotchas

To develop the reusable terraform code, we create modules and those modules can be used accross the environment and teams. For instance, team who wants to ec2 instance within vpc can use vpc and compute modules in their terraform code

To use terraform as a team, we have stored the terraform state in S3 with locking enabled which resolves conflict issues.


