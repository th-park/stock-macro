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

# Run Streamlit
# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "Streamlit not found. Installing dependencies..."
    pip install -r requirements.txt
fi

echo "Starting Stock Dashboard..."
export PYTHONPATH=$PYTHONPATH:.
streamlit run app/dashboard.py
