#!/bin/bash
set -e

service supervisor start
service nginx start

status=$(supervisorctl status focus || true)
if [[ "$status" != *"RUNNING"* && "$status" != *"STARTING"* ]]; then
    supervisorctl start focus
fi

for attempt in {1..30}; do
    status=$(supervisorctl status focus || true)
    if [[ "$status" == *"RUNNING"* ]] && curl -fsS --max-time 2 http://127.0.0.1:8080/ > /dev/null && /opt/focus-venv/bin/python -c 'from pymongo import MongoClient; MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000).admin.command("ping")' 2>/dev/null; then
        echo "$status"
        echo "Site is ready: http://localhost:8080/"
        echo "Keep this window open while using the site. Press Ctrl+C to stop."
        powershell.exe -NoProfile -Command "Start-Process 'http://localhost:8080/'" || true
        exec sleep infinity
    fi
    sleep 1
done

echo "The site or MongoDB did not start. Supervisor status:"
supervisorctl status focus || true
exit 1
