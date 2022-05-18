# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8

EXPOSE 5000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

WORKDIR /portfolio
# Install pip requirements
COPY requirements.txt .
RUN python -m venv venv
RUN venv/bin/pip install --upgrade pip wheel
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
