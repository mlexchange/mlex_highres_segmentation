#!/bin/bash
source .env
export TILED_SINGLE_USER_API_KEY=$DATA_TILED_API_KEY
tiled serve directory data