FROM continuumio/miniconda3 AS builder
COPY env/cpu/py3-master.yml env.yml
RUN conda env create -f env.yml -n ts-dev



FROM debian:latest
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
RUN apt-get update --yes && \
    apt-get install wget curl git --yes && \
    apt-get clean
COPY --from=builder /opt/conda/envs/ts-dev /opt/conda/envs/ts-dev
ENV PATH=/opt/conda/envs/ts-dev/bin:${PATH}

COPY . /root/ts-demand-forecasting
RUN pip install -e /root/ts-demand-forecasting
