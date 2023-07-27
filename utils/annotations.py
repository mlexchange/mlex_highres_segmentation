import numpy as np
from skimage import draw, morphology
import math
from svgpathtools import parse_path
from matplotlib.path import Path
import scipy.sparse as sp
import io

import zipfile


class Annotations:
    def __init__(self, annotation_store):
        self.annotation_store = annotation_store

    def get_annotations(self):
        return self.annotations

    def get_annotation_mask(self):
        return self.annotation_mask

    def get_annotation_mask_as_bytes(self):
        buffer = io.BytesIO()
        zip_buffer = io.BytesIO()
        file_extension = "sp" if self.sparse else "npy"

        # Step 1: Save each numpy array to a separate .npy file in buffer
        npy_files = []
        for i, arr in enumerate(self.annotation_mask):
            npy_buffer = io.BytesIO()
            np.save(npy_buffer, arr)
            npy_files.append((f"mask_{i}.{file_extension}", npy_buffer.getvalue()))

        # Step 2: Add the .npy files to a .zip file using buffer
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for filename, data in npy_files:
                zipf.writestr(filename, data)

        # Get the .zip file data and file extension
        zip_data = zip_buffer.getvalue()

        # Reset the buffer position to the beginning
        buffer.seek(0)
        buffer.write(zip_data)

        return buffer.getvalue()

    def create_annotation_metadata(self):
        """
        This function is responsible for converting the annotation data from the dcc.Store into a format that is compatible with napari annotations.
        """
        annotations = {}
        for image_idx, slice_data in self.annotation_store["annotations"].items():
            annotation_slice = []
            for annotation_idx, shape in enumerate(slice_data):
                self.set_annotation_type(shape)
                self.set_annotation_class(shape)
                self.set_annotation_line_width(shape)
                self.set_annotation_image_shape(image_idx)
                annotation = {
                    "image-id": image_idx,
                    "id": annotation_idx,
                    "type": self.annotation_type,
                    "class": self.annotation_class,
                    "img_shape": self.annotation_image_shape,
                    "line_width": self.annotation_line_width,
                    "brightness": "",
                    "contrast": "",
                }
                annotation_slice.append(annotation)
            annotations[image_idx] = annotation_slice

        self.annotations = annotations

    def create_annotation_mask(self, sparse=False):
        self.sparse = sparse
        annotation_mask = []
        for image_idx, slice_data in self.annotation_store["annotations"].items():
            image_width, image_height = self.annotation_store["image_shapes"][0]
            slice_mask = np.zeros([image_width, image_height], dtype=np.uint8)
            for shape in slice_data:
                self.set_annotation_class(shape)
                self.set_annotation_type(shape)
                self.set_annotation_line_width(shape)
                self.set_annotation_image_shape(image_idx)
                print(self.annotation_class)
                if self.annotation_type == "Closed Freeform":
                    shape_mask = ShapeConversion.closed_path_to_array(
                        shape, self.annotation_image_shape, self.annotation_class
                    )
                elif self.annotation_type == "Freeform":
                    shape_mask = ShapeConversion.opened_path_to_array(
                        shape,
                        self.annotation_image_shape,
                        self.annotation_class,
                        self.annotation_line_width,
                    )
                elif self.annotation_type == "Rectangle":
                    shape_mask = ShapeConversion.rectangle_to_array(
                        shape, self.annotation_image_shape, self.annotation_class
                    )
                elif self.annotation_type == "Ellipse":
                    shape_mask = ShapeConversion.ellipse_to_array(
                        shape, self.annotation_image_shape, self.annotation_class
                    )
                elif self.annotation_type == "Line":
                    shape_mask = ShapeConversion.line_to_array(
                        shape,
                        self.annotation_image_shape,
                        self.annotation_class,
                        self.annotation_line_width,
                    )
                else:
                    continue
                slice_mask[shape_mask > 0] = shape_mask[shape_mask > 0]
            annotation_mask.append(slice_mask)

        if sparse:
            for idx, mask in enumerate(annotation_mask):
                annotation_mask[idx] = sp.csr_array(mask)
        self.annotation_mask = annotation_mask

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

    def set_annotation_line_width(self, annotation):
        """
        This function sets the line width of the annotation.
        """
        self.annotation_line_width = annotation["line"]["width"]

    def set_annotation_class(self, annotation):
        """
        This function sets the class of the annotation.
        """
        self.annotation_class = 99
        for item in self.annotation_store["label_mapping"]:
            if item["color"] == annotation["line"]["color"]:
                self.annotation_class = item["id"]

    def set_annotation_image_shape(self, image_idx):
        """
        This function sets the the size of the image slice
        """
        # TODO: Assuming all images in the slice are the same shape
        self.annotation_image_shape = self.annotation_store["image_shapes"][0]


class ShapeConversion:
    @classmethod
    def ellipse_to_array(self, svg_data, image_shape, mask_class):
        image_width, image_height = image_shape
        x0 = svg_data["x0"]
        y0 = svg_data["y0"]
        x1 = svg_data["x1"]
        y1 = svg_data["y1"]

        # Calculate the radius of the circle (r)
        r = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)

        # Calculate the radius in x-direction (r_radius)
        r_radius = abs(x1 - x0)

        # Calculate the radius in y-direction (c_radius)
        c_radius = abs(y1 - y0)

        # Center of the circle (cx, cy)
        cx = x0
        cy = y0

        # Adjust center coordinates to fit within the image bounds
        cx = max(min(int(cx), image_width - 1), 0)
        cy = max(min(int(cy), image_height - 1), 0)

        r, cx, cy, r_radius, c_radius = int(r), cx, cy, int(r_radius), int(c_radius)

        # Scale the radius if needed to fit within the image bounds
        max_radius = min(cx, cy, image_width - cx, image_height - cy)
        r_radius = min(r_radius, max_radius)
        c_radius = min(c_radius, max_radius)

        # Create the image and draw the circle
        mask = np.zeros((image_width, image_height), dtype=np.uint8)
        rr, cc = draw.ellipse(cy, cx, r_radius, c_radius)

        # Ensure indices are within valid image bounds
        rr = np.clip(rr, 0, image_height - 1)
        cc = np.clip(cc, 0, image_width - 1)

        mask[rr, cc] = mask_class
        return mask

    @classmethod
    def rectangle_to_array(self, svg_data, image_shape, mask_class):
        image_width, image_height = image_shape
        x0 = svg_data["x0"]
        y0 = svg_data["y0"]
        x1 = svg_data["x1"]
        y1 = svg_data["y1"]

        # Adjust coordinates to fit within the image bounds
        x0 = max(min(x0, image_width - 1), 0)
        y0 = max(min(y0, image_height - 1), 0)
        x1 = max(min(x1, image_width - 1), 0)
        y1 = max(min(y1, image_height - 1), 0)

        # # Draw the rectangle
        mask = np.zeros((image_width, image_height), dtype=np.uint8)
        rr, cc = draw.rectangle(start=(y0, x0), end=(y1, x1))

        # Convert coordinates to integers
        rr = np.round(rr).astype(int)
        cc = np.round(cc).astype(int)

        mask[rr, cc] = mask_class
        return mask

    @classmethod
    def line_to_array(self, svg_data, image_shape, mask_class, line_width):
        image_width, image_height = image_shape
        x0 = svg_data["x0"]
        y0 = svg_data["y0"]
        x1 = svg_data["x1"]
        y1 = svg_data["y1"]

        # Adjust coordinates to fit within the image bounds
        x0 = max(min(int(x0), image_width - 1), 0)
        y0 = max(min(int(y0), image_height - 1), 0)
        x1 = max(min(int(x1), image_width - 1), 0)
        y1 = max(min(int(y1), image_height - 1), 0)

        mask = np.zeros((image_width, image_height), dtype=np.uint8)
        rr, cc = draw.line(y0, x0, y1, x1)
        mask[rr, cc] = mask_class
        # mask = morphology.dilation(mask, morphology.disk(radius=line_width))
        return mask

    @classmethod
    def closed_path_to_array(self, svg_data, image_shape, mask_class):
        image_width, image_height = image_shape
        # Parse the SVG path from the input string
        path = parse_path(svg_data["path"])

        # Create a filled polygon using matplotlib
        vertices = []
        for segment in path:
            vertices.extend([segment.start.real, segment.start.imag])
            if hasattr(segment, "control_points"):
                for control_point in segment.control_points:
                    vertices.extend([control_point.real, control_point.imag])

        # Create a matplotlib Path object from the vertices
        polygon_path = Path(np.array(vertices).reshape(-1, 2))

        # Generate a grid of points covering the whole image
        x, y = np.meshgrid(np.arange(0, image_width), np.arange(0, image_height))
        points = np.column_stack((x.ravel(), y.ravel()))

        # Check if each point is inside the polygon
        is_inside = polygon_path.contains_points(points)

        # Reshape the result back into the 2D shape
        mask = is_inside.reshape(image_height, image_width).astype(int)

        # Set the class value for the pixels inside the polygon
        mask[mask == 1] = mask_class

        return mask

    @classmethod
    def opened_path_to_array(self, svg_data, image_shape, mask_class, line_width):
        image_width, image_height = image_shape
        path_data = svg_data["path"]
        path = parse_path(path_data)

        # Create an empty image
        mask = np.zeros((image_width, image_height), dtype=np.uint8)

        # Convert SVG path to points and draw on the image
        for curve in path:
            for t in np.linspace(0, 1, 1000):
                x, y = curve.point(t).real, curve.point(t).imag
                x = max(min(int(x), image_width - 1), 0)
                y = max(min(int(y), image_height - 1), 0)
                mask[y, x] = mask_class
        # mask = morphology.dilation(mask, morphology.disk(radius=line_width))
        return mask
