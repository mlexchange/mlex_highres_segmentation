import os
import sys

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from matplotlib.colors import ListedColormap
from tiled.client import from_uri


def plot_mask(mask_uri, api_key, slice_idx, output_path):
    """
    Saves a plot of a given mask using metadata information such as class colors and labels.
    It is assumed that the given uri is the uri of a mask container, with associated meta data
    and a mask array under the key "mask".
    The given slice index references mask slices, not the original data.
    However, the printed slice index in the figure will be the index of the original data.
    """
    # Retrieve mask and metadata
    mask_client = from_uri(mask_uri, api_key=api_key)
    mask = mask_client["mask"][slice_idx]

    meta_data = mask_client.metadata
    mask_idx = meta_data["mask_idx"]

    if slice_idx > len(mask_idx):
        raise ValueError("Slice index out of range")

    class_meta_data = meta_data["classes"]
    max_class_id = len(class_meta_data.keys()) - 1

    colors = [
        annotation_class["color"] for _, annotation_class in class_meta_data.items()
    ]
    labels = [
        annotation_class["label"] for _, annotation_class in class_meta_data.items()
    ]
    # Add color for unlabeled pixels
    colors = ["#D3D3D3"] + colors
    labels = ["Unlabeled"] + labels

    plt.imshow(
        mask,
        cmap=ListedColormap(colors),
        vmin=-1.5,
        vmax=max_class_id + 0.5,
    )
    plt.title(meta_data["project_name"] + ", slice: " + mask_idx[slice_idx])

    # create a patch for every color
    patches = [
        mpatches.Patch(color=colors[i], label=labels[i]) for i in range(len(labels))
    ]
    # Plot legend below the image
    plt.legend(
        handles=patches, loc="upper center", bbox_to_anchor=(0.5, -0.075), ncol=3
    )
    plt.savefig(output_path, bbox_inches="tight")


if __name__ == "__main__":
    """
    Example usage: python3 plot_mask.py http://localhost:8000/api/v1/metadata/mlex_store/username/dataset/hash
    """

    load_dotenv()
    api_key = os.getenv("MASK_TILED_API_KEY", None)

    if len(sys.argv) < 2:
        print("Usage: python3 plot_mask.py <mask_uri> [slice_idx] [output_path]")
        sys.exit(1)

    mask_uri = sys.argv[1]
    slice_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    output_path = sys.argv[3] if len(sys.argv) > 3 else "mask.png"

    plot_mask(mask_uri, api_key, slice_idx, output_path)
