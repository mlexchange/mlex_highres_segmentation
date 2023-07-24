import math
import numpy as np
from skimage.draw import polygon, circle, polygon_perimeter, line

import re


class Annotations:
    def __init__(self, annotation_store):
        self.annotation_store = annotation_store

    def get_annotations(self):
        return self.annotations

    def create_annotation_metadata(self):
        """
        This function is responsible for converting the annotation data from the dcc.Store into a format that is compatible with napari annotations.
        """
        annotations = {}
        for image_idx, shapes in self.annotation_store["annotations"].items():
            annotation_slice = []
            for annotation_idx, shape in enumerate(shapes):
                self.set_annotation_type(shape)
                self.set_annotation_class(shape)
                self.set_annotation_image_shape(image_idx)
                annotation = {
                    "image-id": image_idx,
                    "id": annotation_idx,
                    "type": self.annotation_type,
                    "class": self.annotation_class,
                    "img_shape": self.annotation_image_shape,
                    "brightness": "",
                    "contrast": "",
                }
                annotation_slice.append(annotation)
            annotations[image_idx] = annotation_slice

        self.annotations = annotations

    def create_annotation_mask(self):
        pass

    def set_annotation_type(self, annotation):
        """
        This function returns readable annotation type name.
        """
        annotation_type = annotation["type"]

        if annotation_type == "path" and "fillrule" in annotation:
            annot = "Closed Freeform"
        elif annotation_type == "path":
            annot = "Freeform"
        elif annotation_type == "rect":
            annot = "Rectangle"
        elif annotation_type == "circle":
            annot = "Ellipse"
        elif annotation_type == "line":
            annot = "Line"
        else:
            annot = "Unknown"

        self.annotation_type = annot

    def set_annotation_class(self, annotation):
        """
        This function sets the class of the annotation.
        """
        map_color_to_class = {
            "rgba(240, 62, 62, 0.3)": 0,
            "#ae3ec9": 1,
            "#7048e8": 2,
            "#1c7ed6": 3,
            "#f59f00": 4,
            "rgba(245, 159, 0, 0.3)": 5,
        }
        self.annotation_class = map_color_to_class[annotation["line"]["color"]]

    def set_annotation_image_shape(self, image_idx):
        """
        This function sets the the size of the image slice
        """
        self.annotation_image_shape = self.annotation_store["image_shapes"][
            int(image_idx)
        ]
