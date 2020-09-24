FROM continuumio/miniconda3 AS builder

COPY env/cpu/py3-master.yml env.yml
RUN conda env create -f env.yml -n ts-dev


FROM debian:latest

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN apt-get update --yes && \
    apt-get install git --yes && \
    apt-get clean

COPY --from=builder /opt/conda/envs/ts-dev /opt/conda/envs/ts-dev

COPY .  /root/ts-demand-forecasting
RUN  /opt/conda/envs/ts-dev/bin/pip install -e /root/ts-demand-forecasting

ENTRYPOINT ["/opt/conda/envs/ts-dev/bin/ts-fcast", "-c", "/root/config/cfg.yml", "-cd", "file"]
CMD ["train", "-i", "/root/config/train.yml", "-id", "file"]