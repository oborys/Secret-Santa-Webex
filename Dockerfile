FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.7
RUN apk --update add bash nano
ENV TZ Europe/Kiev
COPY ./requirements.txt /var/www/requirements.txt
RUN pip install -r /var/www/requirements.txt
