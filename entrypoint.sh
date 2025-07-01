#!/bin/bash

whoami

#Ensure db is there in case of first run
touch data/monitoring.db

if ! [ -e config/config.yaml ]; then
    cp config_sample.yaml config/config.yaml
fi

# Start monitor in background
python monitor.py &

# Start Streamlit dashboard
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
