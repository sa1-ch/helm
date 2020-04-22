## Airflow with LocalExecutor

1. Install mysql and mysqlclient(pymysql)
2. Change sql_alchemy_conn = mysql connection string in airflow.cfg
3. Change executor = LocalExecutor in airflow.cfg.
  
DAG Info:
eks-airflow/dags/kube_airflow_sleep.py

After the above config, do the following

airflow initdb
airflow webserver -p 8080
airflow scheduler


## EKS Cloud Autoscaler:

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

## passing secrets and configMap from Airflow

create secrets in eks:

kubectl create secret generic airflow-secrets --from-literal=cred_file='test.yml'

create configMap in eks:

kubectl create configmap fulltrain-config --from-file=<local path of config file>
  
# sample code to mount the configMap in the dag:
#volume mount
volume_mount_config = VolumeMount(name="config-volume",mount_path="/yum-config/",sub_path=None,read_only=False)
config_dict_sec  = {"configMap":{"name":"fulltrain-config"}}

#volume for configMap
volume_sec = Volume(name="config-volume",configs=config_dict_sec)

volume_mount_list = [volume_mount_config]
volume_list=[volume_sec]

#add volume and volumeMount to KubernetesOperator
passing = KubernetesPodOperator(namespace='default',

                          image="vdinesh1990/kube_airflow_secrets:v2",

                          cmds=None,

                          arguments=[week_day],

                          volume_mounts=volume_mount_list,

                          volumes=volume_list,

                          secrets=[secret_env],

                          labels={"foo": "bar"},

                          name="airflow-k8-secrets",

                          task_id="airflow-k8-secrets"+week_day,

                          in_cluster=False,

                          config_file="/home/dinesh.velmuruga/.kube/config",

                          get_logs=True,

                          dag=dag

                          )




