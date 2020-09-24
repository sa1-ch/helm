## Pushing docker image to ECR

#### 1. Configure aws credentials
```bash
    vi ~/.aws/config
    vi ~/.aws/credentials
```

#### 2. Execute the below command to get the docker login command
```bash
    aws ecr get-login --no-include-email --region us-east-1 | bash
```
<u>*Execute the `docker-login-output` from the above command*</u>


#### 3. Execute the below sequence of commands to push the latest-code-docker-image to ECR `171774164293.dkr.ecr.us-east-1.amazonaws.com/` as `ts-app:TS16`.

##### 3.1. Go to the root-directory
```bash
    cd ./../..
```

##### 3.2. Remove the already available tagged-image
```bash
    docker rmi --force 171774164293.dkr.ecr.us-east-1.amazonaws.com/ts-app:TS16
```

##### 3.3. Build docker image without cache
```bash
    docker build -f deploy/container/Dockerfile -t 171774164293.dkr.ecr.us-east-1.amazonaws.com/ts-app:TS16 . --no-cache
```

##### 3.4. Push the built docker image to ECR
```bash
    docker push 171774164293.dkr.ecr.us-east-1.amazonaws.com/ts-app:TS17
```
