#!/usr/bin/env python3

import json, os

"""This script will compare the botocore library to the collected dataset to find undocumented parameters"""

BOTOCORE_MODELS = "./botocore/botocore/data"
MODELS_DIR = "./models"
botocore = {}
models = {}


if "botocore" not in os.listdir("."):
    print(f"Error! Please download botocore locally")
    exit()


def find_shape(model, shape_name, previous_shape):
    flatlist = []

    if model['shapes'][shape_name]['type'] == "structure":
        for member in model['shapes'][shape_name]['members'].keys():
            # To prevent infinite recursion scenarios, break out here
            # Example: https://github.com/boto/botocore/blob/bc89f1540e0cbb000561a72d20de9df0e92b9f4d/botocore/data/lexv2-runtime/2020-08-07/service-2.json#L532
            if shape_name == model['shapes'][shape_name]['members'][member]['shape']:
                continue
            flatlist += find_shape(model, model['shapes'][shape_name]['members'][member]['shape'], member)
            flatlist.append(previous_shape)
    else:
        flatlist.append(previous_shape)

    return flatlist


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

# Let's recursively search for missing params
for model_name, model in botocore.items():
    if model['metadata']['uid'] not in models.keys():
        continue
    scraped_model = models[model['metadata']['uid']]

    for operation_name, operation in model['operations'].items():
        if 'input' not in operation.keys():
            continue
        if operation_name not in scraped_model['operations'].keys():
            continue

        botocore_params = find_shape(model, operation['input']['shape'], "")
        # EC2 is annoying because it uses mixed case for the scraped model and 
        # Camel case for the botocore library. As a safety precaution but 
        # everything to lower
        botocore_params = [x.lower() for x in botocore_params]

        if 'input' not in scraped_model['operations'][operation_name].keys():
            continue
        if 'members' not in scraped_model['operations'][operation_name]['input'].keys():
            continue

        for param in scraped_model['operations'][operation_name]['input']['members'].keys():
            if param.lower() not in botocore_params:
                print(f"Missing param: {model['metadata']['uid']}:{operation_name}:{param}")
