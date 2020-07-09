# Create EC2 instance within VPC and Subnet

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
(base)$ cd MLE-Playground/terraform/ec2
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

Above comand creates the vpc, subnets, internet gateway, route tables and its output will be stored in variables as in output.tf. Moreover, tf state will be stored in **staging/vpc/terraform.tfstate** with outputs. We do this since we need output of vpc like vpc_id and subnet_id while creating ec2 instance.

### Create EC2 instance

Check the plan that it includes all resource in terraform script
```
(base)$ cd live/staging/compute
(base)$ terraform init
(base)$ terraform plan
```

```
(base)$ terraform apply
```
Once review the plan and apply. Double check and type "yes"

Above comand creates the ec2 instance and its output will be stored in variables as in output.tf. Moreover, tf state will be stored in **staging/compute/terraform.tfstate** with outputs. We do this since we need output of instance like instance_id and avaliablility zone while creating and attaching ebs volume instance that we do in next step.

### Create EBS volume

Check the plan that it includes all resource in terraform script
```
(base)$ cd live/staging/storage
(base)$ terraform init
(base)$ terraform plan
```

```
(base)$ terraform apply
```
Once review the plan and apply. Double check and type "yes"

Above comand creates the ebs volume. Moreover, tf state will be stored in **staging/storage/terraform.tfstate**

### Gotchas

To develop the reusable terraform code, we create modules and those modules can be used accross the environment and teams. For instance, team who wants to ec2 instance within vpc can use vpc and compute modules in their terraform code

To use terraform as a team, we have stored the terraform state in S3 with locking enabled which resolves conflict issues.
