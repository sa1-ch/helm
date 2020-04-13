from airflow import DAG
from datetime import datetime, timedelta
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
from airflow.contrib.kubernetes.volume import Volume
from airflow.contrib.kubernetes.volume_mount import VolumeMount

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
    'kubernetes_sample', default_args=default_args, schedule_interval=None)

volume_mount = VolumeMount(name="docker-sock-volume",mount_path="/var/run/docker.sock",sub_path=None,read_only=False)
config_dict = {"hostPath": {"path": "/var/run/docker.sock","type": "File"}}
volume = Volume(name="docker-sock-volume",configs=config_dict)
volume_mount_list = [volume_mount]
volume_list=[volume]

start = DummyOperator(task_id='run_this_first', dag=dag)

passing = KubernetesPodOperator(namespace='default',
                          image="vdinesh1990/test_airflow:v1",
                          cmds=None,
                          arguments=["52"],
                          volume_mounts=volume_mount_list,
                          volumes=volume_list,
                          labels={"foo": "bar"},
                          name="passing-test",
                          task_id="passing-task",
                          in_cluster=False,
                          config_file="/home/dinesh.velmuruga/.kube/config",
                          get_logs=True,
                          dag=dag
                          )
passing.set_upstream(start)
