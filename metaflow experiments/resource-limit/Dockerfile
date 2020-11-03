FROM continuumio/miniconda3 

RUN pip install metaflow
RUN pip install pandas

WORKDIR /root

COPY .metaflowconfig /root/.metaflowconfig
ENV AWS_DEFAULT_REGION=us-east-1
ENV USERNAME=mle-user
ENV RUN_BATCH=y

COPY . .