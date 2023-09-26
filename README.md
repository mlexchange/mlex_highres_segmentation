# Dash App for Segmentation of High-Resolution Images [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1)](https://pycqa.github.io/isort/)


This application is built using Plotly's [Dash](https://dash.plotly.com/) framework and provides a web-based interface for visualizing and annotating high resolution images output from [ALS](https://als.lbl.gov/) beamlines. 

Image data is accessed via a [Tiled](https://github.com/bluesky/tiled) client, which provides chunkwise access to multidimensional TIFF sequences. 

![plot](assets/preview.png)

## How to use?

### Local development setup

1. Create a new Python virtual environment and install the project dependencies:

```
pip install -r requirements.txt
```

and 

```
pip install -r requirements-dev.txt
```

2. Set environment variables via a `.env` file to configure a connection to the Tiled server, differentiate between local testing and development mode and set a user and password for basic autherization:

```
TILED_URI='https://tiled-seg.als.lbl.gov'
TILED_API_KEY=<key-provided-on-request>
MODE='dev'
USER_NAME=<to-be-specified-per-deployment>
USER_PASSWORD=<to-be-specified-per-deployment>
```

3. Start a local server: 

```
python app.py
```

### Local tiled connection

Developers may also choose to set up a local Tiled server with access to minimal datasets (eg. in the case that the remote server is down).

To start local tiled connection:
1. Add `SERVE_LOCALLY=True` flag to `.env` file (or to your environmental variables)
2. Start the app once, which will create `data/` directory and download 2 sample projects with 2 images each.
3. Open a second terminal and run `tiled serve directory --public data`.

The app will now connect to the local tiled server.

# Copyright
MLExchange Copyright (c) 2023, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Dept. of Energy). All rights reserved.

If you have questions about your rights to use or distribute this software, please contact Berkeley Lab's Intellectual Property Office at IPO@lbl.gov.

NOTICE.  This Software was developed under funding from the U.S. Department of Energy and the U.S. Government consequently retains certain rights.  As such, the U.S. Government has been granted for itself and others acting on its behalf a paid-up, nonexclusive, irrevocable, worldwide license in the Software to reproduce, distribute copies to the public, prepare derivative works, and perform publicly and display publicly, and to permit others to do so.
