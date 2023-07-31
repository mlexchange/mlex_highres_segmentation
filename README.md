# Dash-App for Segmentation of High-Resolution Images
...

## How to use?

### Local development setup

1. Create a new Python virtual environment and install the project dependencies:

```
pip install -r requirements.txt
```

2. Configure a connection to the Tiled server via a `.env` file with the following environment variables:

```
TILED_URI=https://mlex-segmentation.als.lbl.gov
API_KEY=<key-provided-on-request>
```

3. Start a local server: 

```
python app.py
```

### Local tiled connection

To start local tiled connection:
1. Add `SERVE_LOCALLY=True` flag to `env` file (or to your environmental variables)
2. Start the app once, which will create `data/` directory and download 2 sample projects with 2 images each.
3. Open a second terminal and run `tiled serve directory --public data`.

The app will now connect to the local tiled server.

# Copyright
MLExchange Copyright (c) 2023, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Dept. of Energy). All rights reserved.

If you have questions about your rights to use or distribute this software, please contact Berkeley Lab's Intellectual Property Office at IPO@lbl.gov.

NOTICE.  This Software was developed under funding from the U.S. Department of Energy and the U.S. Government consequently retains certain rights.  As such, the U.S. Government has been granted for itself and others acting on its behalf a paid-up, nonexclusive, irrevocable, worldwide license in the Software to reproduce, distribute copies to the public, prepare derivative works, and perform publicly and display publicly, and to permit others to do so.
