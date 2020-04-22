#Airflow with LocalExecutor

1. Install mysql and mysqlclient(pymysql)
2. Change sql_alchemy_conn = mysql connection string in airflow.cfg
3. Change executor = LocalExecutor in airflow.cfg.
  
DAG Info:
eks-airflow/dags/kube_airflow_sleep.py

After the above config, do the following

airflow initdb
airflow webserver -p 8080
airflow scheduler


EKS Cloud Autoscaler:

Create cluster without nodegroup:
*****************************create cluster without-nodegroup********************************
eksctl create cluster --name mle-demo-v1 --version 1.15 --without-nodegroup --region us-east-1 --zones us-east-1a,us-east-1b --without-nodegroup

Create managed node group with auto scaling group access:

******************************create node group**********************************************

eksctl create nodegroup \
--cluster mle-demo-v1 \
--node-zones us-east-1a \
--name mle-us-east-1a \
--asg-access \
--nodes-min 1 \
--nodes 2 \
--nodes-max 4 \
--managed

To create a Cluster Autoscaler deployment, run the following command:
kubectl apply -f eks-airflow/autoscale/cluster-autoscaler-autodiscover.yaml

above command creates the autoscaler deployment.

check the logs using below commands for any error:

kubectl logs -f deployment/cluster-autoscaler -n kube-system


