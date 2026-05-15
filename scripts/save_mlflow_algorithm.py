import argparse
import json
import logging
import os
import sys

from dotenv import load_dotenv

# Add the project root directory to Python path to fix imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mlex_utils.mlflow_utils.mlflow_algorithm_client import (  # noqa: E402
    MlflowAlgorithmClient,
)

# Load environment variables from .env file
load_dotenv(dotenv_path="../.env")

# MLflow Configuration from environment variables
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI_OUTSIDE", "http://localhost:5000")
MLFLOW_TRACKING_USERNAME = os.getenv("MLFLOW_TRACKING_USERNAME", "")
MLFLOW_TRACKING_PASSWORD = os.getenv("MLFLOW_TRACKING_PASSWORD", "")
# Algorithm JSON path from environment variable
ALGORITHM_JSON_PATH = os.getenv("ALGORITHM_JSON_PATH", "../assets/models.json")


# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_mlflow_connection(tracking_uri=None, username=None, password=None):
    """Test MLflow connection and return client if successful"""
    # Use provided parameters or fall back to environment variables
    tracking_uri = tracking_uri or MLFLOW_TRACKING_URI
    username = username or MLFLOW_TRACKING_USERNAME
    password = password or MLFLOW_TRACKING_PASSWORD

    logger.info(f"Testing MLflow connection to {tracking_uri}")
    mlflow_algorithm_client = MlflowAlgorithmClient(tracking_uri, username, password)

    if mlflow_algorithm_client.check_mlflow_ready():
        logger.info("✅ MLflow connection successful")
        return mlflow_algorithm_client
    else:
        logger.error("❌ MLflow connection failed")
        return None


def migrate_all_algorithms(
    overwrite=False, tracking_uri=None, username=None, password=None, json_path=None
):
    """Migrate all algorithms from default_models.json to MLflow"""
    client = test_mlflow_connection(tracking_uri, username, password)
    if not client:
        return False

    # Load algorithms from JSON
    try:
        json_path = json_path or ALGORITHM_JSON_PATH
        logger.info(f"Loading algorithms from: {json_path}")
        with open(json_path) as f:
            data = json.load(f)

        # Handle both formats: with "contents" or direct array
        if "contents" in data:
            algorithms = data["contents"]
        elif isinstance(data, list):
            algorithms = data
        else:
            logger.error(f"Unrecognized JSON format in {json_path}")
            return False

        logger.info(f"Found {len(algorithms)} algorithms in JSON file")
    except Exception as e:
        logger.error(f"Failed to load algorithms from JSON: {e}")
        return False

    # Resolve logo paths relative to the assets directory before registering
    assets_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"
    )

    # Register each algorithm in MLflow
    success_count = 0
    skip_count = 0
    for algorithm in algorithms:
        try:
            # Resolve logo_path and pass as separate kwarg so the algorithm dict
            # is never mutated and logo_path never appears in algorithm_config.json
            logo_filename = algorithm.get("logo")
            logo_path = os.path.join(assets_dir, logo_filename) if logo_filename else None

            result = client.register_algorithm(
                algorithm, overwrite=overwrite, logo_path=logo_path
            )
            if result["status"] == "success":
                logger.info(
                    f"Migrated {algorithm['model_name']} (version {result['version']})"
                )
                success_count += 1
            elif result["status"] == "exists":
                logger.info(f"Skipped {algorithm['model_name']} (already exists)")
                skip_count += 1
            else:
                logger.warning(
                    f"Failed to migrate {algorithm['model_name']}: {result.get('error')}"
                )
        except Exception as e:
            logger.error(
                f"Error migrating {algorithm.get('model_name', 'unknown')}: {e}"
            )

    # Reload once after all algorithms are registered so the cache reflects
    # only the latest versions without intermediate re-downloads per algorithm
    client.load_from_mlflow()

    logger.info(f"Migration completed: {success_count} migrated, {skip_count} skipped")
    return success_count > 0


def list_algorithms(tracking_uri=None, username=None, password=None):
    """List all algorithms in the registry"""
    client = test_mlflow_connection(tracking_uri, username, password)
    if not client:
        return False

    # Load algorithms from MLflow
    client.load_from_mlflow()

    logger.info(f"Found {len(client.algorithm_names)} algorithms in registry:")
    for name in client.algorithm_names:
        algorithm = client[name]
        logger.info(
            f"  - {name} (v{algorithm.get('version', 'unknown')}): {algorithm.get('description', 'No description')}"
        )

    return True


def main():
    """Main function to execute list and migrate commands"""
    parser = argparse.ArgumentParser(description="Migrate algorithms to MLflow")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="If set, register a new version even if the algorithm already exists in MLflow. Default: False.",
    )
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Extract MLflow connection params from environment variables
    tracking_uri = MLFLOW_TRACKING_URI
    username = MLFLOW_TRACKING_USERNAME
    password = MLFLOW_TRACKING_PASSWORD

    # First, list all existing algorithms
    logger.info("Listing existing algorithms in MLflow...")
    list_algorithms(tracking_uri, username, password)

    # Then, migrate algorithms from JSON
    logger.info("\nMigrating algorithms from JSON to MLflow...")
    migrate_all_algorithms(
        overwrite=args.overwrite,
        tracking_uri=tracking_uri,
        username=username,
        password=password,
        json_path=ALGORITHM_JSON_PATH,
    )


if __name__ == "__main__":
    main()
