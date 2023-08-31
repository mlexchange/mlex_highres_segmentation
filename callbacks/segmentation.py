from dash import callback, Input, Output, State, no_update
from utils.annotations import Annotations
from utils.data_utils import get_data_sequence_by_name
import numpy as np


# NEXT STEPS:
# - this function returns a job ID, which would be associated with the workflow run on vaughan
# - then we need another callback to pick up this ID and start polling for successful output
@callback(
    Output("output-placeholder", "children"),
    Input("run-model", "n_clicks"),
    State("annotation-store", "data"),
    State("project-name-src", "value"),
)
def run_job(n_clicks, annotation_store, project_name):
    # As a placeholder, pulling together the inputs we'd need if we were going to submit a job
    if n_clicks:
        annotations = Annotations(annotation_store)
        annotations.create_annotation_metadata()
        annotations.create_annotation_mask(
            sparse=False
        )  # TODO: Would sparse need to be true?

        # Get metadata and annotation data
        metadata = annotations.get_annotations()
        mask = annotations.get_annotation_mask()

        # Get raw images associated with each annotated slice
        # Actually we can just pass the indices and have the job point to Tiled directly
        img_idx = list(metadata.keys())
        img = get_data_sequence_by_name(project_name)
        raw = []
        for idx in img_idx:
            ar = img[int(idx)]
            raw.append(ar)
        try:
            raw = np.stack(raw)
            mask = np.stack(mask)
        except ValueError:
            return "No annotations to process."

        # Some checks to validate that things are in the format we'd expect
        print(metadata)
        print(mask.shape)
        print(raw.shape)

        return "Running the model..."
    return no_update
