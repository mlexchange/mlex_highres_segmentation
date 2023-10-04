#!/bin/bash
source .env
export TILED_SINGLE_USER_API_KEY=$TILED_API_KEY
tiled serve directory data