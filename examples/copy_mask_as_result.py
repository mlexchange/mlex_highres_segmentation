import os
import sys

import numpy as np
from dotenv import load_dotenv
from tiled.client import from_uri

load_dotenv()

MASK_TILED_API_KEY = os.getenv("MASK_TILED_API_KEY")
SEG_TILED_URI = os.getenv("SEG_TILED_URI")
SEG_TILED_API_KEY = os.getenv("SEG_TILED_API_KEY")


def copy_mask_as_result(mask_uri, job_id, quick_inference=True):
    mask_client = from_uri(mask_uri, api_key=SEG_TILED_API_KEY)
    mask = mask_client["mask"][:]
    mask_metadata = mask_client.metadata

    print(
        f"Copying mask with unique values: {np.unique(mask)} and shape: {mask.shape}."
    )

    result_client = from_uri(SEG_TILED_URI, api_key=SEG_TILED_API_KEY)

    result_container = result_client.create_container(key=job_id)
    result_metadata = {
        "data_uri": mask_metadata["data_uri"],
        "mask_uri": mask_uri,
        "mask_idx": mask_metadata["mask_idx"],
    }

    if not quick_inference:
        mask_shape = mask.shape
        image_shape = mask_metadata["image_shape"]

        repeats_needed = image_shape[0] // mask_shape[0]
        partial_repeats_needed = image_shape[0] % mask_shape[0]

        if partial_repeats_needed > 0:
            full_repeats_mask = np.repeat(mask, repeats_needed, axis=0)
            # Take a slice of the mask for the partial repeat
            partial_mask = mask[:partial_repeats_needed, :, :]
            # Concatenate the full repeats and the partial repeat
            mask = np.concatenate((full_repeats_mask, partial_mask), axis=0)
        else:
            # If no partial repeats needed, just use full repeats
            mask = np.repeat(mask, repeats_needed, axis=0)

    result_container.write_array(key="seg_result", array=mask, metadata=result_metadata)


if __name__ == "__main__":
    """
    Example usage: python3 copy_mask_as_result.py http://localhost:8000/api/v1/metadata/mlex_store/username/dataset/hash job_id
    """

    if len(sys.argv) < 3:
        print(
            "Usage: python3 copy_mask_as_result <mask_uri> <job_id> [quick_inference]"
        )
        sys.exit(1)

    mask_uri = sys.argv[1]
    job_id = sys.argv[2]
    if len(sys.argv) < 4:
        quick_inference = True
    else:
        quick_inference = True if sys.argv[3] == 0 else False

    copy_mask_as_result(mask_uri, job_id, quick_inference)
