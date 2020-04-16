Airflow with LocalExecutor

1. Install mysql and mysqlclient(pymysql)
2. Change sql_alchemy_conn = <mysql connection string> airflow.cfg
3. Change executor = LocalExecutor in airflow.cfg.
  
DAG Info:
eks-airflow/dags/kube_airflow_sleep.py

After the above config, do the following

airflow initdb
airflow webserver -p 8080
airflow scheduler


