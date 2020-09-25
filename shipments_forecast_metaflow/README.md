# Shipment_Forecasting -- Metaflow -- Code

## 1. Setup

Create environment with requirements

```bash
    conda env create -f deploy/env/py37_dev.yml -n ship-mf-env
    conda activate ship-mf-env
    sudo apt install graphviz
```  
    

## 2. Configure aws cli for boto3
```bash
    aws configure
```

## 3. Build Shipments-Docker into ECR
```bash
    # Please refer deploy/docker/README.md
```

----------------------------------------------------------------

## 4. Configure metaflow with aws
```bash
    metaflow configure aws  # Please refer values in deploy/cloud-formation/config.json

    cat ~/.metaflowconfig/config.json  # Verify the setup using this command
```


## 5. Push Shipments' docker to ECR
```bash
    sudo docker login -u AWS -p $(aws ecr get-login-password) https://171774164293.dkr.ecr.us-east-1.amazonaws.com
    sudo docker build -f deploy/container/Dockerfile -t 171774164293.dkr.ecr.us-east-1.amazonaws.com/shipment_forecast:metaflow01 .
    sudo docker push 171774164293.dkr.ecr.us-east-1.amazonaws.com/shipment_forecast:metaflow01
```


## 6. Run dag locally
```bash
    python shipments_flow.py show
    python shipments_flow.py run
```


## 7. Run dag in batch
```bash
    python shipments_flow.py show
    python shipments_flow.py run --with batch
```


## 8. Create dag as Step-Function
```bash
    python shipments_flow.py --with retry step-functions create
```

# 9. Trigger Step-Function
```bash
    python shipments_flow.py step-functions trigger
```


## 10. List runs from Step-Function
```bash
    python shipments_flow.py step-functions list-runs
```

## 11. Resume Failed dag, Run-Id <<sfn-1568bb71-2fb7-4560-80b8-0b3f2b5e8cbd>>
```bash
    python shipments_flow.py resume --origin-run-id sfn-1568bb71-2fb7-4560-80b8-0b3f2b5e8cbd --with batch
```


## 12. Export dag as Image
```bash
   python shipments_flow.py output-dot | dot -Tpng -o graph.png
```

## 13. To know job stats, pls refer, `job_status.ipynb`