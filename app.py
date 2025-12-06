import os
import tempfile

# Configure logging at the earliest possible point
import logging
import sys

# Set up basic configuration
logging.basicConfig(
    level=logging.INFO,  # Use DEBUG to see all logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Create logger for this module
logger = logging.getLogger("seg")
logger.info("Logging configured. Frontend module initializing.")

# Explicitly set level for seg namespace
logging.getLogger("seg").setLevel(logging.INFO)

# Force propagation for all existing seg loggers
for name in logging.root.manager.loggerDict:
    if name.startswith('seg.'):
        logging.getLogger(name).propagate = True

import dash_auth
import dash_mantine_components as dmc
from dash import Dash
from flask import send_file
from mlex_utils.mlflow_utils.mlflow_model_client import MLflowModelClient

from callbacks.control_bar import *  # noqa: F403, F401
from callbacks.image_viewer import *  # noqa: F403, F401
from callbacks.infrastructure_check import *  # noqa: F403, F401
from callbacks.segmentation import *  # noqa: F403, F401
from components.control_bar import layout as control_bar_layout
from components.image_viewer import layout as image_viewer_layout

USER_NAME = os.getenv("USER_NAME")
USER_PASSWORD = os.getenv("USER_PASSWORD")

VALID_USER_NAME_PASSWORD_PAIRS = {USER_NAME: USER_PASSWORD}

app = Dash(__name__, update_title=None)
server = app.server

# Initialize MLflow client for serving artifacts
mlflow_client = MLflowModelClient()

# Set single user name password pair if deployment isn't local
auth = (
    dash_auth.BasicAuth(app, VALID_USER_NAME_PASSWORD_PAIRS)
    if os.getenv("DASH_DEPLOYMENT_LOC", "") != "Local"
    else None
)

app.layout = dmc.MantineProvider(
    theme={"colorScheme": "light"},
    children=[
        control_bar_layout(),
        image_viewer_layout(),
    ],
)


@server.route("/mlflow-artifact/<run_id>/<path:artifact_path>")
def serve_mlflow_artifact(run_id, artifact_path):
    """Download and serve MLflow artifacts"""
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            downloaded_path = mlflow_client.client.download_artifacts(
                run_id, artifact_path, tmp_dir
            )
            return send_file(downloaded_path)
    except Exception as e:
        print(f"Error loading MLflow artifact: {e}")
        return f"Error loading artifact: {str(e)}", 404


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8075, debug=True)
