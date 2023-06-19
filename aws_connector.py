import requests, logging, re, json, os

from datetime import datetime

def parse_service_model(js_content, download_location, save, MODEL_DIR):
    match1 = re.findall("(parse\('{\"version\":\"[\.0-9]*?\",.*?'\))", js_content)
    match2 = re.findall("(parse\('{\"metadata\":{\".*?'\))", js_content)
    matches = match1 + match2

    if len(matches) == 0:
        return

    for model in matches:
        # This is necessary to remove 2 trailing characters
        # and to replace some invalid JSON characters
        try:
            parsed_model = json.loads(model[7:-2].replace("\\",""))
        except json.decoder.JSONDecodeError as e:
            logging.warning(f"{datetime.now()} ERROR - Failed to parse: {model[7:-2]} from {download_location}")
            continue

        if 'metadata' not in parsed_model.keys():
            logging.info(f"{datetime.now()} ERROR - No metadata found - {parsed_model}")
            continue

        if 'operations' not in parsed_model.keys():
            logging.info(f"{datetime.now()} ERROR - No operations found - {parsed_model}")
            continue

        # TODO: Better handling for non-uid models (<1%)
        if "uid" not in parsed_model['metadata'].keys():
            if "serviceFullName" in parsed_model['metadata'].keys():
                #logging.info(f"[-] No UID found - {parsed_model['metadata']['serviceFullName']}")
                filename = f"{parsed_model['metadata']['serviceFullName']}-{parsed_model['metadata']['protocol']}"
            else:
                logging.info(f"{datetime.now()} ERROR - No UID found - unnamed")
                filename = "".join([item for item in parsed_model['metadata'].values() if type(item) is str])
            #_mark_download_location(parsed_model, download_location)
            _dump_to_file(parsed_model, filename, './incomplete') 
            continue
        
        if not save:
            # Just print it
            print(json.dumps(parsed_model, indent=4))
        # Need to determine if we have this file already
        elif os.path.exists(f"{MODEL_DIR}/{parsed_model['metadata']['uid']}-{parsed_model['metadata']['protocol']}.json"):
            # Integrate
            # TODO: there are some with alternative serviceFullNames and perhaps other info
            # Need to explore if there is enough of them to have special handling here.
            filename = f"{parsed_model['metadata']['uid']}-{parsed_model['metadata']['protocol']}"
            existing_model = _load_file(filename, MODEL_DIR)

            # Need to mark downloads from the new one before integrating
            parsed_model = _mark_download_location(parsed_model, download_location)
            complete_model = _integrate_models(parsed_model, existing_model)
            _dump_to_file(complete_model, filename, MODEL_DIR)
        else:
            logging.info(f"{datetime.now()} INFO - New model found: {parsed_model['metadata']['uid']}")
            parsed_model = _mark_download_location(parsed_model, download_location)
            filename = f"{parsed_model['metadata']['uid']}-{parsed_model['metadata']['protocol']}"
            _dump_to_file(parsed_model, filename, MODEL_DIR)


def fetch_service_model(javascript_url):
    try:
        resp = requests.get(javascript_url, timeout=30)
    except Exception as e:
        logging.error(f"{datetime.now()} ERROR - Failed to retrieve {javascript_url} {e}")
        return None

    if resp.status_code != 200:
        logging.error(f"{datetime.now()} ERROR - Failed to retrieve {javascript_url}")
    return resp.text


def fetch_services():
    resp = requests.get("https://us-east-1.console.aws.amazon.com/console/home?region=us-east-1&region=us-east-1")
    # 400 is not a bug. This gives the content we want :)
    if resp.status_code != 400:
        logging.critical("[X] Failed to pull service list")
        logging.critical("[X] Exiting")
        exit()
    
    match = re.findall("name=\"awsc-mezz-data\" content='(.*?)'", resp.text)
    return json.loads(match[0])['services']


def process_url(service):
    if "url" not in service.keys():
        logging.error(f"[!] url not in keys for {service}")
        return None
    elif service['url'] is None:
        return None
    elif service['url'][0] == "/":
        return f"https://us-east-1.console.aws.amazon.com{service['url']}?region=us-east-1"
    else:
        return service['url']


def add_endpoints(driver_content, endpoints):
    match = re.findall("(?:\w+ndpoint)&quot;\s*:\s*&quot;\s*([^&]+)", driver_content)
    for item in match:
        endpoints.add(item)
    return endpoints


def find_javascript(driver_content):
    match = re.findall("(https?:\/\/[\w\-._~:\/?#\[\]@!$&'()*+,;=]+\.js)", driver_content)
    return match


def _mark_download_location(model, download_location):
    if 'download_location' not in model['metadata'].keys():
        model['metadata']['download_location'] = [download_location]
    elif download_location not in model['metadata']['download_location']:
        if len(model['metadata']['download_location']) >= 25:
            model['metadata']['download_location'] = model['metadata']['download_location'][:24]
        model['metadata']['download_location'].append(download_location)

    for operation in model['operations']:
        if 'download_location' not in model['operations'][operation].keys():
            model['operations'][operation]['download_location'] = [download_location]
        elif download_location not in model['operations'][operation]['download_location']:
            if len(model['metadata']['download_location']) >= 25:
                model['metadata']['download_location'] = model['metadata']['download_location'][:24]
            model['operations'][operation]['download_location'].append(download_location)

    return model

        
def _load_file(filename, MODEL_DIR):
    with open(f"{MODEL_DIR}/{filename}.json", "r") as r:
        return json.load(r)


def _dump_to_file(model, filename, MODEL_DIR):
    filename = f"{MODEL_DIR}/{filename}.json"
    with open(filename, "w") as w:
        json.dump(model, w, indent=4)


def _integrate_models(parsed_model, existing_model):
    # First, update the download location for the metadata
    if parsed_model['metadata']['download_location'][0] not in existing_model['metadata']['download_location']:
        if len(existing_model['metadata']['download_location']) >= 25:
            existing_model['metadata']['download_location'] = existing_model['metadata']['download_location'][1:]

        existing_model['metadata']['download_location'] += parsed_model['metadata']['download_location']

    # Next deal with operations
    for operation in parsed_model['operations']:
        if operation not in existing_model['operations'].keys():
            logging.info(f"{datetime.now()} INFO - Adding new operation: {existing_model['metadata']['uid']}:{operation}")
            existing_model['operations'][operation] = parsed_model['operations'][operation]

        else:
            if len(existing_model['operations'][operation]['download_location']) >= 25:
                existing_model['operations'][operation]['download_location'] = existing_model['operations'][operation]['download_location'][1:]

            # This operation already exists, but let's update its download_location
            if parsed_model['operations'][operation]['download_location'][0] not in existing_model['operations'][operation]['download_location']:
                existing_model['operations'][operation]['download_location'] += (parsed_model['operations'][operation]['download_location'])

            # This operation already exists, so let's integrate its parameters
            if 'input' in parsed_model['operations'][operation].keys() and 'members' in parsed_model['operations'][operation]['input'].keys():
                for member in parsed_model['operations'][operation]['input']['members'].keys():
                    if 'members' not in existing_model['operations'][operation]['input'].keys():
                        existing_model['operations'][operation]['input']['members'] = {}

                    if member not in existing_model['operations'][operation]['input']['members'].keys():
                        existing_model['operations'][operation]['input']['members'][member] = parsed_model['operations'][operation]['input']['members'][member]
                        logging.info(f"{datetime.now()} INFO - Adding new input parameter: {existing_model['metadata']['uid']}:{operation}:{member}")

    # Now add new shapes
    for shape in parsed_model['shapes']:
        if shape not in existing_model['shapes'].keys():
            existing_model['shapes'][shape] = parsed_model['shapes'][shape]
    
    return existing_model
