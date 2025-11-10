import logging
import os
import shutil
import hashlib
import tempfile  

import mlflow
from mlex_utils.prefect_utils.core import get_flow_run_name
from mlflow.tracking import MlflowClient

from utils.prefect import get_flow_run_parent_id

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")
MLFLOW_TRACKING_USERNAME = os.getenv("MLFLOW_TRACKING_USERNAME", "")
MLFLOW_TRACKING_PASSWORD = os.getenv("MLFLOW_TRACKING_PASSWORD", "")
# Define a cache directory that will be mounted as a volume
MLFLOW_CACHE_DIR = os.getenv("MLFLOW_CACHE_DIR", os.path.join(tempfile.gettempdir(), "mlflow_cache"))

logger = logging.getLogger(__name__)


class MLflowClient:
    """A wrapper class for MLflow client operations."""
    
    # In-memory model cache (for quick access)
    _model_cache = {}
    
    def __init__(
        self, 
        tracking_uri=None,
        username=None, 
        password=None,
        cache_dir=None
    ):
        """
        Initialize the MLflow client with connection parameters.
        
        Args:
            tracking_uri: MLflow tracking server URI
            username: MLflow authentication username
            password: MLflow authentication password
            cache_dir: Directory to store cached models
        """
        self.tracking_uri = tracking_uri or os.getenv("MLFLOW_TRACKING_URI")
        self.username = username or os.getenv("MLFLOW_TRACKING_USERNAME", "")
        self.password = password or os.getenv("MLFLOW_TRACKING_PASSWORD", "")
        self.cache_dir = cache_dir or MLFLOW_CACHE_DIR
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Set environment variables
        os.environ['MLFLOW_TRACKING_USERNAME'] = self.username
        os.environ['MLFLOW_TRACKING_PASSWORD'] = self.password
        
        # Set tracking URI
        mlflow.set_tracking_uri(self.tracking_uri)
        
        # Create client
        self.client = MlflowClient()

    def check_mlflow_ready(self):
        """
        Check if MLflow server is reachable by performing a lightweight API call.
        
        Returns:
            bool: True if MLflow server is reachable, False otherwise
        """
        try:
            # Perform a lightweight API call to verify connectivity
            # search_experiments() is a simple call that requires minimal server resources
            self.client.search_experiments(max_results=1)
            logger.info("MLflow server is reachable")
            return True
        except Exception as e:
            logger.warning(f"MLflow server is not reachable: {e}")
            return False

    def get_mlflow_params(self, mlflow_model_id):
        model_version_details = self.client.get_model_version(
            name=mlflow_model_id,  # The registered model name
            version="1",  # The version you care about
        )
        run_id = model_version_details.run_id

        run_info = self.client.get_run(run_id)
        params = run_info.data.params
        return params

    def get_mlflow_models(self, livemode=False, model_type=None):
        """
        Retrieve available MLflow models and create dropdown options.

        Args:
            livemode (bool): If True, only include models where exp_type == "live_mode".
                            If False, exclude models where exp_type == "live_mode" and use custom labels.
            model_type (str, optional): Filter by run tag 'model_type'.

        Returns:
            list: Dropdown options for MLflow models matching the tag filters.
        """
        try:
            all_versions = self.client.search_model_versions()

            model_map = {}  # model name -> latest version info

            for v in all_versions:
                try:
                    current = model_map.get(v.name)
                    if current and int(v.version) <= int(current.version):
                        continue

                    run = self.client.get_run(v.run_id)
                    run_tags = run.data.tags

                    # Tag-based filtering
                    exp_type = run_tags.get("exp_type")
                    if livemode:
                        if exp_type != "live_mode":
                            continue
                    else:
                        if exp_type == "live_mode":
                            continue

                    if model_type is not None and run_tags.get("model_type") != model_type:
                        continue

                    model_map[v.name] = v

                except Exception as e:
                    logger.warning(f"Error processing model version {v.name} v{v.version}: {e}")
                    continue

            # Build dropdown options
            model_options = []
            for name in sorted(model_map.keys()):
                if livemode:
                    label = name
                else:
                    try:
                        parent_id = get_flow_run_parent_id(name)
                        label = get_flow_run_name(parent_id)
                    except Exception as e:
                        logger.warning(f"Failed to get label for model '{name}': {e}")
                        label = name  # fallback

                model_options.append({"label": label, "value": name})

            return model_options

        except Exception as e:
            logger.warning(f"Error retrieving MLflow models: {e}")
            return [{"label": "Error loading models", "value": None}]

    def _get_cache_path(self, model_name, version=None):
        """Get the cache path for a model"""
        # Create a unique filename based on model name and version
        if version is None:
            # Use a hash of the model name as part of the filename
            hash_obj = hashlib.md5(model_name.encode())
            hash_str = hash_obj.hexdigest()
            return os.path.join(self.cache_dir, f"{model_name}_{hash_str}")
        else:
            # Include version in the filename
            return os.path.join(self.cache_dir, f"{model_name}_v{version}")

    def load_model(self, model_name):
        """
        Load a model from MLflow by name with disk caching
        
        Args:
            model_name: Name of the model in MLflow
            
        Returns:
            The loaded model or None if loading fails
        """
        if model_name is None:
            logger.error("Cannot load model: model_name is None")
            return None
        
        # Check in-memory cache first
        if model_name in self._model_cache:
            logger.info(f"Using in-memory cached model: {model_name}")
            return self._model_cache[model_name]
        
        try:
            # Get latest version using existing client
            versions = self.client.search_model_versions(f"name='{model_name}'")
            
            if not versions:
                logger.error(f"No versions found for model {model_name}")
                return None
                
            latest_version = max([int(mv.version) for mv in versions])
            model_uri = f"models:/{model_name}/{latest_version}"
            
            # Check disk cache
            cache_path = self._get_cache_path(model_name, latest_version)
            if os.path.exists(cache_path):
                logger.info(f"Loading model from disk cache: {cache_path}")
                try:
                    # Load from cached MLflow model
                    model = mlflow.pyfunc.load_model(cache_path)
                    
                    # Store in memory cache
                    self._model_cache[model_name] = model
                    
                    logger.info(f"Successfully loaded cached model: {model_name}")
                    return model
                except Exception as e:
                    logger.warning(f"Error loading model from cache: {e}")
                    # Continue to download if cache load fails
            
            # Create cache directory if it doesn't exist
            os.makedirs(os.path.dirname(cache_path) if os.path.dirname(cache_path) else ".", exist_ok=True)
            
            # Instead of loading and then saving, we'll download directly to the cache location
            # This is more efficient and avoids the save_model error
            logger.info(f"Downloading model {model_name}, version {latest_version} from MLflow to cache")
            
            # Use mlflow.artifacts.download_artifacts to get the model artifacts
            try:
                # First method: Download the model directly to the cache location
                download_path = mlflow.artifacts.download_artifacts(
                    artifact_uri=f"models:/{model_name}/{latest_version}",
                    dst_path=cache_path
                )
                logger.info(f"Downloaded model artifacts to: {download_path}")
                
                # Now load the model from the cached location
                model = mlflow.pyfunc.load_model(download_path)
                logger.info(f"Successfully loaded model from cache: {model_name}")
                
                # Store in memory cache
                self._model_cache[model_name] = model
                
                return model
            except Exception as e:
                logger.warning(f"Error downloading artifacts: {e}")
                
                # Fallback: Load the model directly from MLflow if download fails
                logger.info(f"Falling back to direct model loading from MLflow")
                model = mlflow.pyfunc.load_model(model_uri)
                logger.info(f"Successfully loaded model: {model_name}")
                
                # Store in memory cache
                self._model_cache[model_name] = model
                
                return model
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return None
    
    @classmethod
    def clear_memory_cache(cls):
        """Clear the in-memory model cache"""
        logger.info("Clearing in-memory model cache")
        cls._model_cache.clear()
    
    def clear_disk_cache(self):
        """Clear the disk cache"""
        logger.info(f"Clearing disk cache at {self.cache_dir}")
        try:
            # Delete and recreate the cache directory
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Error clearing disk cache: {e}")