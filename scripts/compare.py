#!/usr/bin/env python3

"""This script will compare results found in the AWS Console to the botocore dataset.
   Doing this may reveal API actions that are undocumented."""

# NOTE: I intentionally remove some botocore data that does not have a UID. 
# This is to make things easier but it may have an attack surface. Go back and review

import os, json

BOTOCORE_MODELS = "./botocore/botocore/data"
MODELS_DIR = "./models"
botocore = {}


if "botocore" not in os.listdir("."):
    print(f"Error! Please download botocore locally")
    exit()

# Slurp all botocore models into memory
# with `uid` as the primary key
for service in os.listdir(BOTOCORE_MODELS):
    if not os.path.isdir(f"{BOTOCORE_MODELS}/{service}"):
        continue

    for version in os.listdir(f"{BOTOCORE_MODELS}/{service}/"):
        if not os.path.isdir(f"{BOTOCORE_MODELS}/{service}/{version}"):
            continue

        if not os.path.exists(f"{BOTOCORE_MODELS}/{service}/{version}/service-2.json"):
            continue

        with open(f"{BOTOCORE_MODELS}/{service}/{version}/service-2.json", "r") as r:
            data = json.load(r)
            if 'uid' not in data['metadata'].keys():
                continue
            botocore[data['metadata']['uid']] = data

# Search through all crawled model definitions and compare to botocore
# If something is not in botocore, alert

# We print in the weird format to support markdown linking

modelfiles = os.listdir(MODELS_DIR)
for file in modelfiles:
    with open(f"{MODELS_DIR}/{file}", "r") as r:
        data = json.load(r)
    
    # First check if the UID exists in botocore. If not, all operations are free game
    if data['metadata']['uid'] not in botocore.keys():
        print(f"{data['metadata']['uid']} not found  ")
        for operation in data['operations'].keys():
            print(f"[v]({MODELS_DIR}/{file}) - {data['metadata']['uid']}:{operation}  ")
    
    # Next, if the uid's match, compare the operations
    elif data['metadata']['uid'] in botocore.keys():
        for operation in data['operations']:
            if operation not in botocore[data['metadata']['uid']]['operations'].keys():
                print(f"[v]({MODELS_DIR}/{file}) - {data['metadata']['uid']}:{operation}  ")
