#!/usr/bin/env python3

import json, os

BOTOCORE_MODELS = "./botocore/botocore/data"
MODELS_DIR = "./models"
botocore = {}
models = {}


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

# Now slurp our rendered models
for model in os.listdir(MODELS_DIR):
    with open(f"{MODELS_DIR}/{model}", "r") as r:
        data = json.load(r)
        if 'uid' not in data['metadata'].keys():
            continue
        models[data['metadata']['uid']] = data 

# Now let's compare the two
for model_name, model in models.items():
    if model['metadata']['uid'] not in botocore.keys():
        continue

    for operation_name, operation in model['operations'].items():
        if 'input' not in operation.keys() or 'members' not in operation['input'].keys():
            continue
        for param in operation['input']['members'].keys():
            if operation_name not in botocore[model['metadata']['uid']]['operations'].keys():
                continue
            if "input" not in botocore[model['metadata']['uid']]['operations'][operation_name].keys():
                continue
            print(botocore[model['metadata']['uid']]['operations'][operation_name]['input'])

            if param not in botocore[model['metadata']['uid']]['operations'][operation_name]['input']['members'].keys():
                print(f"Missing param: {param} in {model_name}::{operation_name}")