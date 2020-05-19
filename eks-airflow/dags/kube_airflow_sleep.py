import random
from airflow import DAG
from datetime import datetime, timedelta
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
from airflow.contrib.kubernetes.volume import Volume
from airflow.contrib.kubernetes.volume_mount import VolumeMount
from airflow.operators.python_operator import BranchPythonOperator

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
    'kubernetes_airflow_branch', default_args=default_args, schedule_interval=None)

volume_mount = VolumeMount(name="docker-sock-volume",mount_path="/var/run/docker.sock",sub_path=None,read_only=False)
config_dict = {"hostPath": {"path": "/var/run/docker.sock","type": "File"}}
volume = Volume(name="docker-sock-volume",configs=config_dict)
volume_mount_list = [volume_mount]
volume_list=[volume]

week_options = [random.randint(1, 10) for iter in range(10)]

start = DummyOperator(task_id='run_this_first', dag=dag)

#week_options = ["branch_01","branch_02","branch_03","branch_04"]

#branching = BranchPythonOperator(
#    task_id='branching',
#    python_callable=lambda: random.choice(week_options),
#    dag=dag,
#)

#start >> branching

join = DummyOperator(
    task_id='join',
    trigger_rule='none_failed_or_skipped',
    dag=dag,
)

for int_week_option in week_options:
    week_option = str(int_week_option)
    t = DummyOperator(
        task_id="dummy-"+week_option,
        dag=dag,
    )

    #week_day = week_option.split("_")[1]
    week_day = week_option
    passing = KubernetesPodOperator(namespace='default',
                              image="vdinesh1990/test_airflow_sleep:v1",
                              cmds=None,
                              arguments=[week_day],
                              volume_mounts=volume_mount_list,
                              volumes=volume_list,
                              labels={"kube_label": "kube_sleep"},
                              name="passing-test",
                              task_id="kube-week-"+week_day,
                              in_cluster=False,
                              config_file="/home/dinesh.velmuruga/.kube/config",
                              get_logs=True,
                              dag=dag
    )
    start >> passing >> t >> join

