import os
import json
import requests
from constants import DATA


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

    print("Downloading sample data...")
    if not os.path.exists(base_directory):
        os.makedirs(base_directory)

    for project, urls in sample_data_links.items():
        project_directory = os.path.join(base_directory, project)
        if not os.path.exists(project_directory):
            os.makedirs(project_directory)

        for i, url in enumerate(urls):
            destination = os.path.join(project_directory, f"{i}.tiff")

            if os.path.exists(destination):
                print(f"File {destination} already exists. Skipping download.")
                continue

            download_file(url, destination)
            print(f"Downloaded {destination}")

    print("All files downloaded successfully.")


def DEV_load_exported_json_data(file_path, USER_NAME, PROJECT_NAME):
    """
    This function is used to load the exported json, which was saved in a local file.
    User name is used to filter the data by user.
    Project name is used to filter the data by project.
    It is sorted by timestamp with the latest timestamp first.

    TODO: this function will be replaced with a database query in the future.
    """
    DATA_JSON = []

    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                json_data = json.loads(line)
                json_data["data"] = json.loads(json_data["data"])
                DATA_JSON.append(json_data)

    data = [
        data
        for data in DATA_JSON
        if data["user"] == USER_NAME and data["source"] == PROJECT_NAME
    ]
    if data:
        data = sorted(data, key=lambda x: x["time"], reverse=True)

    return data


def DEV_filter_json_data_by_timestamp(data, timestamp):
    return [data for data in data if data["time"] == timestamp]


def get_data_project_names():
    return list(DATA)
