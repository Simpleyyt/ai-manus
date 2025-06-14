#!/bin/bash

exec uvicorn app.main:app --host 0.0.0.0 --port 8000  --timeout-graceful-shutdown 5