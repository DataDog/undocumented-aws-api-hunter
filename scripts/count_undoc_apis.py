#!/usr/bin/env python3

"""This script will compare results found in the AWS Console to the botocore dataset.
   Doing this may reveal API actions that are undocumented."""

# NOTE: I intentionally remove some botocore data that does not have a UID. 
# This is to make things easier but it may have an attack surface. Go back and review

import os, json, sys

if len(sys.argv) < 3:
    print(f"Usage: ./count_undoc_apis.py <botocore path> <models paths>")
    exit()

if "botocore" not in os.listdir("."):
    print(f"Error! Please download botocore locally")
    exit()

BOTOCORE_MODELS = f"{os.path.expanduser(sys.argv[1])}/botocore/data"
MODELS_DIR = os.path.expanduser(sys.argv[2])
botocore = {}

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

######################################################################################
# Count undocumented services
# Methodology: This should be simple, we check the uid of each model and split on the first -20 or -19. 
# For example, SSO-2017-11-28 would be SSO. cleanrooms-2022-02-17 would be cleanrooms. giraffe-1986-04-08 
# would be giraffe. This will help separate the service from the version.
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


######################################################################################
# Count undocumented versions of documented services
# Methodology: This will be slightly more complicated as we need to first check if a service 
# is documented and if it is, we then need to see if the version is undocumented.
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



######################################################################################
# Count undocumented parameters for documented actions
# Methodology: Substantially more complex than previous. We compare services by their UID 
# and by their actions. If an extracted model has a parameter that the documented model does not have, 
# we count that as an undocumented parameter. I know the code is rough below. When it comes to parameters 
# the extracted model file format differs from the documented models. This means I can't use the same 
# recursive function. I have taken steps to double check this output to make sure nothing is amiss.

# VERY IMPORTANT: This does NOT enumerate all sub-parameters. You cannot (realistically) do this with the current model format.
# As an example lambda-2015-03-32:UpdateFunctionEventInvokeConfig has the parameter DestinationConfig, this has a 
# sub-parameter OnSuccess, which itself has a member for "Destination".
# https://github.com/Frichetten/aws-api-models/blob/4bc7b764593d2c2b78e3f81ff8c7027bd7048e50/models/lambda-2015-03-31-rest-json.json#L4358
# In botocore all of this is still true, however it continues on. "Destination" has a sub-member for "DestinationArn"
# https://github.com/boto/botocore/blob/0ac30565017f1486b2eebf9bd90b5411f0d7f1fb/botocore/data/lambda/2015-03-31/service-2.json#L4747
# Because of these model differences we can never reconcile this.

# If you find a way to reliably (emphasis) do this, please let me know. I would love to hear about it.
# For now, we are only comparing the top level parameters. This has the knock-on effect of reporting 
# fewer undocumented parameters than there actually are.

# Below you will find find_shape and find_member. These are recursive functions left over from when I was trying to find 
# all sub-parameters. They are not used in the final version of this script. I've kept them here for reference if 
# someone (or future me) wants to try and tackle this problem again.
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
    #if service_name != "lambda-2015-03-31":
    #    continue
    if service_name not in extracted_data.keys():
        continue

    for operation_name, operation in service['operations'].items():
        #if operation_name != "UpdateFunctionConfiguration":
        #    continue
        if 'input' not in operation.keys():
            continue
        if operation_name not in extracted_data[service_name]['operations'].keys():
            continue
        if 'input' not in extracted_data[service_name]['operations'][operation_name].keys():
            continue
        if 'members' not in extracted_data[service_name]['operations'][operation_name]['input'].keys():
            continue

        #botocore_params = find_shape(service, operation['input']['shape'], "")
        #print(botocore_params)
        botocore_params = []
        for param_name, param_value in service['shapes'][operation['input']['shape']]['members'].items():
            botocore_params.append(param_name)

        extracted_params = []
        for param_name, param_value in extracted_data[service_name]['operations'][operation_name]['input']['members'].items():
            extracted_params.append(param_name)
        #for param_name, param_value in extracted_data[service_name]['operations'][operation_name]['input']['members'].items():
        #    if "shape" in param_value.keys():
        #        recursive_params = find_member(extracted_data[service_name], param_value['shape'], param_name)
        #        extracted_params += recursive_params
        #    else:
        #        # There are 2 scenarios. The first is that the parameter is a structure. The second is that it is a simple type.
        #        # If it is a structure, we need to extract the members. If it is a simple type, we can just add it to the list.
        #        # If you need a good example of this, check out the "PutBotAlias" action in the "lex-models-2017-04-19" service.
        #        if "type" in param_value.keys() and param_value['type'] == "structure":
        #            for member in param_value['members'].keys():
        #                extracted_params.append(member)
        #        else:
        #            extracted_params.append(param_name)
        #extracted_params = set(extracted_params)
        #print(extracted_params)
            
        for param in extracted_params:
            if param not in botocore_params:
                #print(f"{service_name}:{operation_name}:{param}")
                undocumented_parameters_count += 1
print(f"Undocumented parameters for documented actions: {undocumented_parameters_count}")



######################################################################################
# Count undocumented actions of documented services
# Methodology: Slightly less complex than previous. We compare services by their UID. 
# If an extracted model has an action that the documented model does not have, we count that as an undocumented action.
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



######################################################################################
# Count all undocumented actions for undocumented services
# Methodology: This is the easiest. If the service itself is not documented, all of its actions are undocumented.
# We simply iterate through all of our extracted services and count the actions.
botocore_actions = {}
for service_name, service in botocore.items():
    name = service['metadata']['uid']
    botocore_actions[name] = service['operations']

extracted_actions = {}
for service_name, service in extracted.items():
    name = service['metadata']['uid']
    extracted_actions[name] = service['operations']

#print("Finding undocumented actions for undocumented services")
undocumented_actions_count = 0
for service_name, operations in extracted_actions.items():
    if service_name in botocore_actions.keys():
        continue

    for operation in operations.keys():
        #print(f"{service_name}:{operation}")
        undocumented_actions_count += 1

print(f"Undocumented actions for undocumented services: {undocumented_actions_count}")

