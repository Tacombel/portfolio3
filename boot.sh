#!/bin/bash
source venv/bin/activate
exec gunicorn -b :5000 --timeout 240 --access-logfile - --error-logfile - portfolio3:app