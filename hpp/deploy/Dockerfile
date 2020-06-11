FROM continuumio/miniconda3 AS builder
COPY env/dep-linux.yml env.yml
RUN conda env create -f env.yml -n hpp-docker

FROM debian:latest
ENV FLASK_APP app.py
ENV FLASK_CONFIG docker

RUN adduser mle-user
COPY --from=builder /opt/conda/envs/hpp-docker /opt/conda/envs/hpp-docker

WORKDIR /home/mle-user/hpp-docker
COPY . /home/mle-user/hpp-docker
RUN chown -R mle-user /home/mle-user/hpp-docker
USER mle-user
RUN  /opt/conda/envs/hpp-docker/bin/pip install -e /home/mle-user/hpp-docker

EXPOSE 5000
#start gunicorn which host flask app
ENTRYPOINT ["sh","./start_server.sh"]
