#!/bin/bash
# Activate the correct virtual environment (venv)
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found. Please run 'python3 -m venv venv' and install requirements."
    exit 1
fi

echo "Starting Data Collector..."
export PYTHONPATH=$PYTHONPATH:.
python -m app.data_collector
