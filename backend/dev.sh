#!/bin/bash

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload  --timeout-graceful-shutdown 0