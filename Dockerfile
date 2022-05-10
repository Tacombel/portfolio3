# For more information, please refer to https://aka.ms/vscode-docker-python
FROM ubuntu:20.04

EXPOSE 5000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

WORKDIR /portfolio
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install python3 python3-venv chromium-chromedriver chromium-browser libnss3 libffi-dev libssl-dev libxml2-dev libxslt-dev python3-lxml
# Install pip requirements
COPY requirements.txt .
RUN python3 -m venv venv
RUN venv/bin/pip install wheel
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn
COPY app app
RUN mkdir data
COPY boot.sh config.py portfolio3.py scrape_one.py scrape.py XIRR.py ./
RUN chmod +x boot.sh
RUN adduser -u 5678 --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser ./
USER appuser
ENV FLASK_APP portfolio3.py

ENTRYPOINT ["./boot.sh"]
