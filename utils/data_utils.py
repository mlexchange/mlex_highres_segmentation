import os


def get_data_options(dir="data"):
    return [file for file in os.listdir(f"{dir}/") if file.endswith("tiff")]
