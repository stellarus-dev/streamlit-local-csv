#!/bin/bash
# Startup script for Azure App Service

# Activate pre-built virtual environment from GitHub Actions
source antenv/bin/activate

# Run Streamlit app
streamlit run streamlit_csv.py --server.port=8000 --server.address=0.0.0.0
