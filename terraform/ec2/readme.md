# Create EC2 instance within VPC and Subnet
Above example creates the EC2 instance within vpc and subnets. Moreover, it creates internet gateway, route tables for vpc. Underlyng storage is ebs which is created and attahed to ec2.

To set lots of variables, it is more convenient to specify their values in a variable definitions file (with a filename ending in either .tfvars or .tfvars.json) and then specify that file on the command line with -var-file

```
(base)$ terraform apply -var-file="testing.tfvars.json"
```

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
It is recommended to have terraform state files in remote backend to avoid issues like manual errors, locking and secrets. Remote backends allow you to store the state file in a remote, shared store. We have used S3 to store the terraform state files by enabling encryption and accidental delete.

Create S3 bucket and dynamo db to lock the state during the changes
```
(base)$ cd state
(base)$ terraform init
(base)$ terraform plan
(base)$ terraform apply
```

Above commands creates the S3 bucket and dynamodb

Note: Above step is one time

### Create EC2 instance within vpc and subnet
Create a key pair and place the public key in key.tf

Check the plan that it includes all resource in terraform script
```
(base)$ cd ./ec2
(base)$ terraform init
(base)$ terraform plan
```

Once review the plan and apply. Double check and type "yes"

```
(base)$ terraform apply
```
