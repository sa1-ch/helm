#!/bin/sh
#source venv/bin/activate
#flask deploy
exec /opt/conda/envs/hpp-docker/bin/gunicorn -b 0.0.0.0:5000 --access-logfile - --error-logfile - app:app
