FROM python:3.8
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
RUN apt-get update && apt-get install -y \
 coreutils \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
EXPOSE 80
ENTRYPOINT exec uwsgi --http 0.0.0.0:80 --module config.wsgi --py-autoreload 1 --logto /tmp/mylog.log
