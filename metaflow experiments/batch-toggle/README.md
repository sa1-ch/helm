# McD-Pricing-Engine -- Baseline code in METAFLOW -- Setup

Codes for PoC using Metaflow for Bayesian Models. The currently supports S3 interactions using ```boto3``` library

## 1. Setup

Create environment with requirements

```bash
    conda env create -f deploy/env/cpu/dev.yml -n mcd_baseline
    conda activate mcd_baseline
    sudo yum install graphviz
```  
    

## 2. Configure aws cli for boto3
```bash
    aws configure
```

## 4. Check s3 bucket name in the config.ini (point to the bucket created for mcd metaflow poc):
```bash
    config["s3Config"]["bucket"] = "aws-metaflow-batch"
```

## 5. Specify the output folder and experiment_path in config.ini as stated below (for each new run):
```bash
    config["s3Config"]["output_folder"] = <folder_name>
    config["s3Config"]["experiment_name"] = <experiment name>
```
  A folder with specified experiment name and respective subfolders for outputs would be automatically created during the run.
  An ```output_folder``` can host many experiment folders.
  * kindly donot alter the base path "output_path" to maintain the experiments on s3 with ease

## 6. Running the code (in local code directory)
```bash
    python main.py run
```

## 7. some important config controls that effect data volume and runtimes:
```bash
    congig["runConfig"]["clusters"] = 1,2             : clusters to be modeled (leave it empty to get clusters from input file names)
    congig["runConfig"]["items"] = 4314,6050,6,35     : items to be modeled (leave it empty to get items from input file names)
    
    congig["elasticity_model"]["num_warmup_iters"]  : #Bayesian burnin samples -- 30 for testing -- 300 for actual run (this impacts runtime)
    congig["elasticity_model"]["num_iters"]         : #Bayesian actual samples -- 10 for testing -- 100 for actual run (this impacts runtime)
```
----------------------------------------------------------------

## 3. Configure metaflow with aws
```bash
    metaflow configure aws  # Please refer values in deploy/cloud-formation/config.json

    cat ~/.metaflowconfig/config.json  # Verify the setup using this command
```


## 4. Push Shipments' docker to ECR
```bash
    sudo docker login -u AWS -p $(aws ecr get-login-password) https://171774164293.dkr.ecr.us-east-1.amazonaws.com
    sudo docker build -f deploy/docker/Dockerfile -t 171774164293.dkr.ecr.us-east-1.amazonaws.com/mcd-metaflow-batch:tg03 .
    sudo docker push 171774164293.dkr.ecr.us-east-1.amazonaws.com/mcd-metaflow-batch:tg03
```


## 5. Run dag locally
```bash
    python main.py show
    python main.py run
```


## 6. Run dag in batch
```bash
    python runBayesian.py show
    python runBayesian.py run --with batch
```


## 7. Create dag as Step-Function
```bash
    python runBayesian.py --with retry step-functions create --max-workers 1000
```

# 8. Trigger Step-Function
```bash
    python runBayesian.py step-functions trigger
```


## 9. List runs from Step-Function
```bash
    python main.py step-functions list-runs
```

## 10. Resume Failed dag, Run-Id <<sfn-1568bb71-2fb7-4560-80b8-0b3f2b5e8cbd>>
```bash
    python main.py resume --origin-run-id sfn-1568bb71-2fb7-4560-80b8-0b3f2b5e8cbd --with batch
```


## 11. Export dag as Image
```bash
   python main.py output-dot | dot -Tpng -o graph.png
```

## 12. To know job stats, pls refer, `job_status.ipynb`