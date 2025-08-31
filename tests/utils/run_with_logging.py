#!/usr/bin/env python3
"""Run streamlit app with logging enabled."""

import logging
import sys

# Configure logging to show INFO level messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Now run the streamlit app
import streamlit.cli as stcli

if __name__ == '__main__':
    sys.argv = ["streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"]
    stcli.main()