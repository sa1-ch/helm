# metaflow-template

conda env create -f deploy/env/py37_dev.yml -n metaflow-env

```bash
metaflow tutorials pull
metaflow tutorials list
metaflow tutorials info 00-helloworld

python helloworld.py show
python helloworld.py run

metaflow status
```

```
aws configure
cat ~/.metaflowconfig/config

metaflow configure aws
mcd-dev-1-metaflows3bucket-qe8cybgiof9s

```


aws ecr get-login --no-include-email --region us-east-1 | bash

aws ecr get-login-password

sudo docker login -u AWS -p $(aws ecr get-login-password) https://171774164293.dkr.ecr.us-east-1.amazonaws.com
sudo docker build -f deploy/container/Dockerfile -t 171774164293.dkr.ecr.us-east-1.amazonaws.com/mcd-metaflow:mf03 .
sudo docker push 171774164293.dkr.ecr.us-east-1.amazonaws.com/mcd-metaflow:mf03


python helloworld.py run --with batch

python helloworld.py --with retry step-functions create
python helloworld.py step-functions trigger

https://docs.metaflow.org/getting-started/tutorials/season-1-the-local-experience/episode04
conda config --add channels conda-forge

python helloworld.py resume --origin-run-id sfn-1568bb71-2fb7-4560-80b8-0b3f2b5e8cbd --with batch


metaflow-template$ python helloworld.py output-dot | dot -Tpng -o graph.png

python helloworld.py step-functions list-runs

python helloworld.py resume --origin-run-id sfn-1568bb71-2fb7-4560-80b8-0b3f2b5e8cbd

python debug.py resume --origin-run-id sfn-5ca85f96-8508-409d-a5f5-b567db1040c5 --with batch


python helloworld.py step-functions trigger --origin-run-id sfn-1568bb71-2fb7-4560-80b8-0b3f2b5e8cbd

