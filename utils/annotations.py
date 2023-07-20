import math
import numpy as np


class Annotations:
    def __init__(self, annotation_store):
        self.annotation_store = annotation_store

    def get_annotations(self):
        return self.annotations

    def process_annotation_data(self):
        """
        This function is responsible for converting the annotation data from the dcc.Store into a format that is compatible with napari annotations.
        """
        annotations = []
        for image_idx, shapes in self.annotation_store.items():
            for annotation_idx, shape in enumerate(shapes):
                annotation = {
                    "image-id": image_idx,
                    "id": annotation_idx,
                    "type": self.get_annotation_type(shape),
                    "class": self.get_annotation_class(shape),
                    "brightness": "",
                    "contrast": "",
                    "path": self.get_annotation_path(shape),
                }
                annotations.append(annotation)

        self.annotations = annotations

    def get_annotation_type(self, annotation):
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

        return annot

    def get_annotation_class(self, annotation):
        """
        This function returns the class of the annotation.
        """
        color = annotation["line"]["color"]
        return color

    def get_annotation_path(self, annotation):
        """
        This function returns the path of the annotation.
        """
        if annotation["type"] == "line":
            x0, y0, x1, y1 = (
                annotation["x0"],
                annotation["y0"],
                annotation["x1"],
                annotation["y1"],
            )
            path = f"M{x0},{y0}L{x1},{y1}"
        elif annotation["type"] == "circle":
            path = self.convert_oval_to_path(annotation)
        elif annotation["type"] == "rect":
            x0, y0, x1, y1 = (
                annotation["x0"],
                annotation["y0"],
                annotation["x1"],
                annotation["y1"],
            )
            path = f"M{x0},{y0}L{x1},{y0}L{x1},{y1}L{x0},{y1}Z"
        else:
            path = annotation["path"]
        return path

    def convert_oval_to_path(self, oval_path):
        """
        This function converts an oval (circle) annotation to a path.
        """
        x0, y0, x1, y1 = (
            oval_path["x0"],
            oval_path["y0"],
            oval_path["x1"],
            oval_path["y1"],
        )

        rx = (x1 - x0) / 2  # x-radius
        ry = (y1 - y0) / 2  # y-radius
        cx = (x0 + x1) / 2  # x-coordinate of the center
        cy = (y0 + y1) / 2  # y-coordinate of the center

        num_segments = 100  # Number of segments to approximate the oval

        # Generate the path using cubic Bézier curves
        path = "M"

        for i in range(num_segments):
            angle = 2 * math.pi * (i / num_segments)
            x = cx + rx * math.cos(angle)
            y = cy + ry * math.sin(angle)

            if i == 0:
                path += f"{x},{y}"
            else:
                path += f"C{x - rx * math.cos(angle + math.pi / num_segments) / 2},{y - ry * math.sin(angle + math.pi / num_segments) / 2} "
                path += f"{x + rx * math.cos(angle + math.pi / num_segments) / 2},{y + ry * math.sin(angle + math.pi / num_segments) / 2} "
                path += f"{x},{y}"

        path += "Z"

        return path
