import os


def get_data_options(dir="data"):
    return [file for file in os.listdir(f"{dir}/") if file.endswith("tiff")]


def convert_hex_to_rgba(hex, alpha=0.3):
    return f"rgba{tuple(int(hex[i:i+2], 16) for i in (1, 3, 5)) + (alpha,)}"
