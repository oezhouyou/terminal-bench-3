#!/bin/bash

# Ensure PostgreSQL is running
service postgresql start 2>/dev/null || true
sleep 2

# Kill any existing app process
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 1

# Start the app with the agent's (possibly modified) code
cd /app
/app/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/app.log 2>&1 &
APP_PID=$!

# Wait for app to be ready (up to 30 seconds)
for i in $(seq 1 30); do
    if curl -s "http://localhost:8000/api/products?page=1&per_page=1&category_id=1&sort=id" > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Install test runner and dependencies (curl already available from Dockerfile)
curl -LsSf https://astral.sh/uv/0.9.7/install.sh | sh
source $HOME/.local/bin/env

uvx \
  --with pytest==8.4.1 \
  --with pytest-json-ctrf==0.3.5 \
  --with requests \
  pytest --ctrf /logs/verifier/ctrf.json /tests/test_performance.py -rA -v

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi

kill $APP_PID 2>/dev/null || true
