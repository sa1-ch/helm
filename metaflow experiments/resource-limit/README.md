# Episode 02-statistics: Is this Data Science?

Code for the experiment to limit metaflow resource restriction.

Steps to run:

1. Clone the repository and switch to the **exp/metaflow-resource-limit** branch.

```bash
git clone https://github.com/tigerrepository/MLE-Playground.git && git checkout exp/metaflow-resource-limit
```

2. Build Docker Image

```bash
docker build . -t metaflow_experiment
```

3. Run Docker Image

--cpuset-cpus & -m parameters are used to limit processor and memory usage.

[--cpuset-cpus](https://docs.docker.com/engine/reference/run/#cpuset-constraint) parameter is used to select the cpu cores where the container will run. 0-1 means cores 0 and 1.

[-m](https://docs.docker.com/engine/reference/run/#runtime-constraints-on-resources) limits the memory usage of the container. **10g** is 10 GB.

[--cpus](https://docs.docker.com/config/containers/resource_constraints/#configure-the-default-cfs-scheduler) can be also used to limit the amount of cpu the container gets. For instance, if the host machine has two CPUs and you set --cpus="1.5", the container is guaranteed at most one and a half of the CPUs.

```bash
docker run -d --cpuset-cpus="0-1" -m 10g -v $(pwd)/outputs:/root/outputs metaflow_experiment python stats.py --no-pylint run
```