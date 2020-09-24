### Update Kube-Config

#### update kube-config from cluster, `tiger-mle-eks`
```bash
aws eks --region us-east-1 update-kubeconfig --name tiger-mle-eks
```

-------------------------------------------------------------------------------------------------------

### namespace

#### create
```bash
kubectl apply -f namespaces.yml
```

#### delete
```bash
kubectl delete -f namespaces.yml
```

-------------------------------------------------------------------------------------------------------

### nginx controller

#### create
```bash
kubectl apply -f nginx_controller.yml
```

#### delete
```bash
kubectl delete -f nginx_controller.yml
```

-------------------------------------------------------------------------------------------------------

### create config-map
```bash
    kubectl create configmap eks-deploy-config --namespace=ts-eks-ns \
        --from-literal=rds_db_endpoint=mle-db-instance.cngtflo14uzz.us-east-1.rds.amazonaws.com \
        --from-literal=efs_id=fs-2b3801a8 \
        --from-literal=docker_image_id=171774164293.dkr.ecr.us-east-1.amazonaws.com/ts-app:TS17 \
        --from-literal=alb_endpoint=a451866fc02a64dc8acaf680fcb859f8-5097f0c8c58210ab.elb.us-east-1.amazonaws.com \
        --from-literal=mlflow_artifacts=s3://tiger-mle-tg/mlflow-artifacts \
        --from-literal=airflow_dags=s3://tiger-mle-tg/airflow/dags/ \
        --from-literal=airflow_logs=s3://tiger-mle-tg/airflow/logs/
```

-------------------------------------------------------------------------------------------------------

### auto-scaling groups

#### create
```bash
kubectl apply -f autoscaler.yml
```

#### delete
```bash
kubectl delete -f autoscaler.yml
```

------------------------------------------------------------------------------------------------------
### helm

#### helm stable charts installation
```bash
helm repo add stable https://kubernetes-charts.storage.googleapis.com/
helm repo list
helm repo update
helm search repo
```

-------------------------------------------------------------------------------------------------------
### EFS for PVC

#### Copy and paste the EFS file-system created using terraform
#### create
```bash
cat efs_provisioner.yml | sed "s~{{efs_id}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.efs_id}' -n ts-eks-ns)~g" | kubectl apply -n ts-eks-ns -f -
kubectl apply -f efs_rbac.yml --namespace=ts-eks-ns
kubectl apply -f efs_storage.yml --namespace=ts-eks-ns
```

#### delete
```bash
cat efs_provisioner.yml | sed "s~{{efs_id}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.efs_id}' -n ts-eks-ns)~g" | kubectl delete -n ts-eks-ns -f -
kubectl delete -f efs_rbac.yml --namespace=ts-eks-ns
kubectl delete -f efs_storage.yml --namespace=ts-eks-ns
```

--------------------------------------------------------------------------------------------------------
<!-- ### HTTPS Setup

#### Cert-Manager
```bash
kubectl apply --validate=false -f https://raw.githubusercontent.com/jetstack/cert-manager/release-0.11/deploy/manifests/00-crds.yaml 
kubectl delete -f https://raw.githubusercontent.com/jetstack/cert-manager/release-0.11/deploy/manifests/00-crds.yaml

kubectl create namespace cert-manager

helm repo add jetstack https://charts.jetstack.io
helm repo update

helm install \
  cert-manager \
  --namespace cert-manager \
  --version v0.11.0 \
  jetstack/cert-manager
  
helm uninstall cert-manager --namespace cert-manager
```

#### Cert Issuer
```bash
kubectl apply -f https_issuer.yml

kubectl delete -f https_issuer.yml
```

#### Cert Getter
```bash
kubectl apply -f https_certificate.yml

kubectl delete -f https_certificate.yml
```
 -->
-------------------------------------------------------------------------------------------------------
### K8s Dashboard

#### create
```bash
kubectl apply -f dashboard_metrics.yml
kubectl apply -f dashboard_deploy.yml
kubectl apply -f dashboard_rbac.yml

kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | grep eks-admin | awk '{print $1}')
```

#### delete
```bash
kubectl delete -f dashboard_metrics.yml
kubectl delete -f dashboard_deploy.yml
kubectl delete -f dashboard_rbac.yml
```


#### To be enabled after enabling HTTPS
<!-- ### K8s Dashboard nginx ingress mapping

#### create
```bash
kubectl apply -f dashboard_nginx_ingress.yml --namespace=kubernetes-dashboard
```

#### delete
```bash
kubectl delete -f dashboard_nginx_ingress.yml --namespace=kubernetes-dashboard
``` -->


### K8s Dashboard: run locally
```bash
kubectl proxy --port=8001 --address=0.0.0.0

http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#/login

kubectl port-forward svc/kubernetes-dashboard 8080 -n kubernetes-dashboard --address=0.0.0.0
```

-------------------------------------------------------------------------------------------------------

### Prometheus

#### create
```bash
kubectl create namespace prometheus

helm install prometheus stable/prometheus \
    --namespace prometheus \
    --values prometheus.yml \
    --set nodeSelector.nodegroup-name=app-demand
    
kubectl get deployment -n prometheus prometheus-kube-state-metrics -o yaml | sed "s~      containers:~      nodeSelector:\n        nodegroup-name: app-demand\n      containers:~g" | kubectl apply -n prometheus -f -
```

#### delete
```bash
helm uninstall prometheus -n prometheus
```

### Prometheus: run locally
```bash
kubectl get svc -n prometheus
kubectl port-forward svc/prometheus-server 8888:80 -n prometheus
```

-------------------------------------------------------------------------------------------------------
### Grafana

#### create
```bash
kubectl create namespace grafana

helm install grafana stable/grafana \
    --namespace grafana \
    --values grafana.yml \
    --set datasources."datasources\.yaml".apiVersion=1 \
    --set datasources."datasources\.yaml".datasources[0].name=Prometheus \
    --set datasources."datasources\.yaml".datasources[0].type=prometheus \
    --set datasources."datasources\.yaml".datasources[0].url=http://prometheus-server.prometheus.svc.cluster.local \
    --set datasources."datasources\.yaml".datasources[0].access=proxy \
    --set datasources."datasources\.yaml".datasources[0].isDefault=true \
    --set nodeSelector.nodegroup-name=app-demand
```

#### delete
```bash
helm uninstall grafana -n grafana
```


### K8s Dashboard nginx ingress mapping

#### create
```bash
cat grafana_nginx_ingress.yml | sed "s~{{alb_endpoint}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.alb_endpoint}' -n ts-eks-ns)~g" | kubectl apply -n grafana -f -
```

#### delete
```bash
cat grafana_nginx_ingress.yml | sed "s~{{alb_endpoint}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.alb_endpoint}' -n ts-eks-ns)~g" | kubectl delete -n grafana -f -
```



#### Grafana: run
```bash
kubectl get secret --namespace grafana grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
kubectl get svc grafana -n grafana
https://grafana.com/grafana/dashboards 
choose 10000
```

-------------------------------------------------------------------------------------------------------


### mlflow secrets for mlflow-postgres-server

#### create
```bash
kubectl create secret generic mlflow-postgres-password --from-literal=password='Tiger123!' --namespace=ts-eks-ns
```

#### delete
```bash
kubectl delete secret mlflow-postgres-password --namespace=ts-eks-ns
```


### mlflow server

#### create
```bash
kubectl apply -f mlflow_server.yml --namespace=ts-eks-ns
```

#### delete
```bash
kubectl delete -f mlflow_server.yml --namespace=ts-eks-ns
```


### mlflow server: nginx ingress mapping

#### create
```bash
cat mlflow_nginx_ingress.yml | sed "s~{{alb_endpoint}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.alb_endpoint}' -n ts-eks-ns)~g" | kubectl apply -n ts-eks-ns -f -
```

#### delete
```bash
cat mlflow_nginx_ingress.yml | sed "s~{{alb_endpoint}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.alb_endpoint}' -n ts-eks-ns)~g" | kubectl delete -n ts-eks-ns -f -
```

-------------------------------------------------------------------------------------------------------

### airflow secrets for airflow-postgres-server

#### create
```bash
kubectl create secret generic airflow-postgres-password --from-literal=password='Tiger123!' --namespace=ts-eks-ns
```

#### delete
```bash
kubectl delete secret airflow-postgres-password --namespace=ts-eks-ns
```


### airflow s3-sync, dags & logs

#### create
```bash
kubectl apply -f airflow_logs_sync.yml --namespace=ts-eks-ns
kubectl apply -f airflow_dags_sync.yml --namespace=ts-eks-ns
```

#### delete
```bash
kubectl delete -f airflow_logs_sync.yml --namespace=ts-eks-ns
kubectl delete -f airflow_dags_sync.yml --namespace=ts-eks-ns
```


### airflow-server

#### create
```bash
helm install airflow-server \
  --version 7.1.0 \
  --set externalDatabase.host=$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.rds_db_endpoint}' -n ts-eks-ns) \
  --values airflow_server.yml \
  --namespace=ts-eks-ns \
  stable/airflow
```

#### delete
```bash
helm uninstall airflow-server --namespace=ts-eks-ns
```


### airflow-server: nginx ingress mapping

#### create
```bash
cat airflow_nginx_ingress.yml | sed "s~{{alb_endpoint}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.alb_endpoint}' -n ts-eks-ns)~g" | kubectl apply -n ts-eks-ns -f -
```

#### delete
```bash
cat airflow_nginx_ingress.yml | sed "s~{{alb_endpoint}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.alb_endpoint}' -n ts-eks-ns)~g" | kubectl delete -n ts-eks-ns -f -
```

-------------------------------------------------------------------------------------------------------

### EDA Dashboard

#### create
```bash
cat viz_eda.yml | sed "s~{{docker_image_id}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.docker_image_id}' -n ts-eks-ns)~g" | kubectl apply -n ts-eks-ns -f -
```

#### delete
```bash
cat viz_eda.yml | sed "s~{{docker_image_id}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.docker_image_id}' -n ts-eks-ns)~g" | kubectl delete -n ts-eks-ns -f -
```


### EDA Dashboard: nginx ingress mapping

#### create
```bash
cat viz_eda_nginx.yml | sed "s~{{alb_endpoint}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.alb_endpoint}' -n ts-eks-ns)~g" | kubectl apply -n ts-eks-ns -f -
```

#### delete
```bash
cat viz_eda_nginx.yml | sed "s~{{alb_endpoint}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.alb_endpoint}' -n ts-eks-ns)~g" | kubectl delete -n ts-eks-ns -f -
```

-------------------------------------------------------------------------------------------------------

### MODEL-EVALUATION Dashboard

#### create
```bash
cat viz_eval.yml | sed "s~{{docker_image_id}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.docker_image_id}' -n ts-eks-ns)~g" | kubectl apply -n ts-eks-ns -f -
```

#### delete
```bash
cat viz_eval.yml | sed "s~{{docker_image_id}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.docker_image_id}' -n ts-eks-ns)~g" | kubectl delete -n ts-eks-ns -f -
```


### MODEL-EVALUATION Dashboard: nginx ingress mapping

#### create
```bash
cat viz_eval_nginx.yml | sed "s~{{alb_endpoint}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.alb_endpoint}' -n ts-eks-ns)~g" | kubectl apply -n ts-eks-ns -f -
```

#### delete
```bash
cat viz_eval_nginx.yml | sed "s~{{alb_endpoint}}~$(kubectl get configmap eks-deploy-config -o jsonpath='{.data.alb_endpoint}' -n ts-eks-ns)~g" | kubectl delete -n ts-eks-ns -f -
```

-------------------------------------------------------------------------------------------------------
