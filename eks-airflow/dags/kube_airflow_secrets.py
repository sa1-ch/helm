from airflow import DAG
from datetime import datetime, timedelta
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
from airflow.contrib.kubernetes.volume import Volume
from airflow.contrib.kubernetes.volume_mount import VolumeMount
import random
from airflow.contrib.kubernetes import secret
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(2),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2)    
}

dag = DAG(
    'kubernetes_airflow_secrets', default_args=default_args, schedule_interval=None)

volume_mount = VolumeMount(name="docker-sock-volume",mount_path="/var/run/docker.sock",sub_path=None,read_only=False)
#volume mount for configMap
volume_mount_config = VolumeMount(name="config-volume",mount_path="/yum-config/",sub_path=None,read_only=False)
config_dict = {"hostPath": {"path": "/var/run/docker.sock","type": "File"}}
#configMap created from file
config_dict_sec  = {"configMap":{"name":"fulltrain-config"}}
volume = Volume(name="docker-sock-volume",configs=config_dict)

#volume for configMap
volume_sec = Volume(name="config-volume",configs=config_dict_sec)
volume_mount_list = [volume_mount,volume_mount_config]
volume_list=[volume,volume_sec]

secret_env = secret.Secret(
    # Expose the secret as environment variable.
    deploy_type='env',
    # The name of the environment variable, since deploy_type is `env` rather
    # than `volume`.
    deploy_target='CRED_FILE',
    # Name of the Kubernetes Secret
    secret='airflow-secrets',
    # Key of a secret stored in this Secret object
    key='cred_file')

start = DummyOperator(task_id='run_this_first', dag=dag)
end = DummyOperator(task_id='run_this_last', dag=dag)

week_options = [random.randint(1, 5) for iter in range(5)]

week_options = [str(item) for item in week_options]
week_day = "04"
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
start >> passing >> end
