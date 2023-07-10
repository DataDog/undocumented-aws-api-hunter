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

extracted = {}
modelfiles = os.listdir(MODELS_DIR)
for file in modelfiles:
    with open(f"{MODELS_DIR}/{file}", "r") as r:
        data = json.load(r)
        if 'uid' not in data['metadata'].keys():
            continue
        extracted[data['metadata']['uid']] = data

# Count undocumented services
# Methodology: This should be simple, we check the uid of each model and split on the first -20 or -19. For example, SSO-2017-11-28 would be SSO. cleanrooms-2022-02-17 would be cleanrooms. giraffe-1986-04-08 would be giraffe. This will help separate the service from the version.
botocore_services = set()
for service_name, service in botocore.items():
    name = service['metadata']['uid'].split("-20")[0].split("-19")[0]
    botocore_services.add(name)

extracted_services = set()
for service_name, service in extracted.items():
    name = service['metadata']['uid'].split("-20")[0].split("-19")[0]
    extracted_services.add(name)

#print("Finding undocumented services")
undocumented_services_count = 0
for service in extracted_services:
    if service not in botocore_services:
        #print(service)
        undocumented_services_count += 1
print(f"Undocumented services: {undocumented_services_count}")


# Count undocumented versions of documented services
# Methodology: This will be slightly more complicated as we need to first check if a service is documented and if it is, we then need to see if the version is undocumented.
botocore_services = []
for service_name, service in botocore.items():
    name = service['metadata']['uid']
    botocore_services.append(name)

extracted_services = []
for service_name, service in extracted.items():
    name = service['metadata']['uid']
    extracted_services.append(name)

#print("Finding undocumented service versions for documented services")
undocumented_service_versions_count = 0
for service in extracted_services:
    name = service.split("-20")[0].split("-19")[0]
    found = any(name in substring for substring in botocore_services)
    if not found:
        continue

    if service not in botocore_services:
        #print(service)
        undocumented_service_versions_count += 1
print(f"Undocumented service versions for documented services: {undocumented_service_versions_count}")


# Count undocumented actions of documented services
# Methodology: Slightly less complex than previous. We compare services by their UID. If an extracted model has an action that the documented model does not have, we count that as an undocumented action.
botocore_actions = {}
for service_name, service in botocore.items():
    name = service['metadata']['uid']
    botocore_actions[name] = service['operations']

extracted_actions = {}
for service_name, service in extracted.items():
    name = service['metadata']['uid']
    extracted_actions[name] = service['operations']

#print("Finding undocumented actions for documented services")
undocumented_actions_count = 0
for service_name, operations in extracted_actions.items():
    if service_name not in botocore_actions.keys():
        continue

    for operation in operations.keys():
        if operation in botocore_actions[service_name].keys():
            continue

        #print(f"{service_name}:{operation}")
        undocumented_actions_count += 1
print(f"Undocumented actions for documented services: {undocumented_actions_count}")


# Count undocumented parameters for documented actions
# Methodology: Substantially more complex than previous. We compare services by their UID and by their actions. If an extracted model has a parameter that the documented model does not have, we count that as an undocumented parameter. I know the code is rough below. When it comes to parameters the extracted model file format differs from the documented models. This means I can't use the same recursive function. I have taken steps to double check this output to make sure nothing is amiss.
botocore_data = {}
for service_name, service in botocore.items():
    name = service['metadata']['uid']
    botocore_data[name] = service

extracted_data = {}
for service_name, service in extracted.items():
    name = service['metadata']['uid']
    extracted_data[name] = service

# This function will be used recursively to find the parameter shapes
def find_shape(model, shape_name, previous_shape):
    flatlist = []

    if model['shapes'][shape_name]['type'] == "structure":
        for member in model['shapes'][shape_name]['members'].keys():
            # To prevent infinite recursion scenarios, break out here
            # Example: https://github.com/boto/botocore/blob/bc89f1540e0cbb000561a72d20de9df0e92b9f4d/botocore/data/lexv2-runtime/2020-08-07/service-2.json#L532
            if shape_name == model['shapes'][shape_name]['members'][member]['shape']:
                continue
            flatlist += find_shape(model, model['shapes'][shape_name]['members'][member]['shape'], member)
    else:
        flatlist.append(previous_shape)

    return flatlist


def find_member(model, shape_name, previous_shape):
    flatlist = []

    if model['shapes'][shape_name]['type'] == "structure":
        for member in model['shapes'][shape_name]['members'].keys():
            if 'shape' in model['shapes'][shape_name]['members'][member].keys():
                # Same anti-recursion check
                if shape_name == model['shapes'][shape_name]['members'][member]['shape']:
                    continue
                flatlist += find_member(model, model['shapes'][shape_name]['members'][member]['shape'], member)

            elif "type" in model['shapes'][shape_name]['members'][member].keys() and model['shapes'][shape_name]['members'][member]['type'] == "structure":
                for submember in model['shapes'][shape_name]['members'][member]['members'].keys():
                    flatlist.append(submember)

            else:
                flatlist.append(member)
    else:
        flatlist.append(previous_shape)

    return flatlist

#print("Finding undocumented parameters for documented actions")
undocumented_parameters_count = 0
# Note we iterate the botocore data because we are only interested in documented services
for service_name, service in botocore_data.items():
    if service_name not in extracted_data.keys():
        continue

    for operation_name, operation in service['operations'].items():
        if 'input' not in operation.keys():
            continue
        if operation_name not in extracted_data[service_name]['operations'].keys():
            continue
        if 'input' not in extracted_data[service_name]['operations'][operation_name].keys():
            continue
        if 'members' not in extracted_data[service_name]['operations'][operation_name]['input'].keys():
            continue

        botocore_params = find_shape(service, operation['input']['shape'], "")

        extracted_params = []
        for param_name, param_value in extracted_data[service_name]['operations'][operation_name]['input']['members'].items():
            if "shape" in param_value.keys():
                recursive_params = find_member(extracted_data[service_name], param_value['shape'], param_name)
                extracted_params += recursive_params
            else:
                extracted_params.append(param_name)
        extracted_params = set(extracted_params)
            
        for param in extracted_params:
            if param not in botocore_params:
                #print(f"{service_name}:{operation_name}:{param}")
                undocumented_parameters_count += 1
print(f"Undocumented parameters for documented actions: {undocumented_parameters_count}")


# Count all undocumented actions (from both documented and undocumented services)
# Methodology: This is relatively simple. Iterate through all of our extracted services. If a service does not appear in botocore, all of its actions are considered undocumented. If the service DOES appear in botocore, we compare the actions. If an action appears in our extracted models but not botocore, it's undocumented.
botocore_actions = {}
for service_name, service in botocore.items():
    name = service['metadata']['uid']
    botocore_actions[name] = service['operations']

extracted_actions = {}
for service_name, service in extracted.items():
    name = service['metadata']['uid']
    extracted_actions[name] = service['operations']

#print("Finding undocumented actions for documented/undocumented services")
undocumented_actions_count = 0
for service_uid, operations in extracted_actions.items():
    if service_uid not in botocore_actions.keys():
        # This is an undocumented service, all its actions are fair game
        for operation in operations:
            undocumented_actions_count += 1
            #print(f"{service_uid}:{operation}")
        
    else:
        for operation in operations:
            if operation not in botocore_actions[service_uid].keys():
                undocumented_actions_count += 1
                #print(f"{service_uid}:{operation}")

print(f"Undocumented actions for documented/undocumented actions: {undocumented_actions_count}")
