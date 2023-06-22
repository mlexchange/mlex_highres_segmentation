import os
import requests
from urllib.parse import urlparse


def get_data_project_names(dir="data"):
    return [
        folder for folder in os.listdir(dir) if os.path.isdir(os.path.join(dir, folder))
    ]


def get_tiff_files(folder_path, dir="data"):
    return [
        file for file in os.listdir(f"{dir}/{folder_path}") if file.endswith(".tiff")
    ]


def DEV_download_google_sample_data():
    """
    Download sample project images to data/ folder, this only happens once, after that the download is skipped if the data exists.
    """

    def download_file(url, destination):
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(destination, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

    sample_data_links = {
        "check_handedness": [
            "https://drive.google.com/u/0/uc?id=1l42VFZcmVOITL3-eqCKVX_u3PDc7Vkw7&export=download",
            "https://drive.google.com/u/0/uc?id=1Glio8R-ur65iESK8cvjg7uUHXWnY1odx&export=download",
        ],
        "clay_testZMQ": [
            "https://drive.google.com/u/0/uc?id=1TnVfWOUZNu4aYsoaJYvOB6lP0KW6fEou&export=download",
            "https://drive.google.com/u/0/uc?id=19Y37JxpUwXlWCC2O5mJNsZftzpy_E8te&export=download",
        ],
    }
    base_directory = "data"

    # print("Downloading sample data...")
    if not os.path.exists(base_directory):
        os.makedirs(base_directory)

    for project, urls in sample_data_links.items():
        project_directory = os.path.join(base_directory, project)
        if not os.path.exists(project_directory):
            os.makedirs(project_directory)

        for i, url in enumerate(urls):
            filename = urlparse(url).path.split("/")[-1]
            destination = os.path.join(project_directory, f"{filename}_{i}.tiff")

            if os.path.exists(destination):
                # print(f"File {destination} already exists. Skipping download.")
                continue

            download_file(url, destination)
            # print(f"Downloaded {destination}")

    # print("All files downloaded successfully.")


def convert_hex_to_rgba(hex, alpha=0.3):
    return f"rgba{tuple(int(hex[i:i+2], 16) for i in (1, 3, 5)) + (alpha,)}"
