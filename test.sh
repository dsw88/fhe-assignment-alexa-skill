#!/bin/bash

export DYNAMODB_FHE_ALEXA_PRD_DB_TABLE_NAME=fhe-alexa-prd-db-dynamodb

VERBOSE=False
if [ "$1" == "verbose" ]; then
    VERBOSE=True
fi

python lambda_function.py test --verbose $VERBOSE
