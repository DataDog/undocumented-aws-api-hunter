import requests, logging, re, json, os

def parse_service_model(js_content, download_location, save, MODEL_DIR):
    match = re.findall("({\"version\":\"[\.0-9]*?\",.*?'\))", js_content)
    if len(match) == 0:
        return

    for model in match:
        # This is necessary to remove 2 trailing characters
        # and to replace some invalid JSON caracters
        try:
            parsed_model = json.loads(model[:-2].replace("\\",""))
        except json.decoder.JSONDecodeError as e:
            logging.warning(f"[!] Failed to parse: {model[:-2]} from {download_location}")
            continue

        if 'metadata' not in parsed_model.keys():
            logging.info(f"[-] No metadata found - {parsed_model}")
            continue

        # TODO: Better handling for non-uid models (<1%)
        if "uid" not in parsed_model['metadata'].keys():
            logging.info(f"[-] No UID found - {parsed_model['metadata']['serviceFullName']}")
            continue
        
        if not save:
            # Just print it
            print(json.dumps(parsed_model, indent=4))
        # Need to determine if we have this file already
        elif os.path.exists(f"{MODEL_DIR}/{parsed_model['metadata']['uid']}.json"):
            # Integrate
            # TODO: there are some with alternative serviceFullNames and perhaps other info
            # Need to explore if there is enough of them to have special handling here.
            filename = f"{parsed_model['metadata']['uid']}"
            existing_model = _load_file(filename, MODEL_DIR)

            # Need to mark downloads from the new one before integrating
            parsed_model = _mark_download_location(parsed_model, download_location)
            complete_model = _integrate_models(parsed_model, existing_model, download_location)
            _dump_to_file(complete_model, download_location, filename, MODEL_DIR)
        else:
            parsed_model = _mark_download_location(parsed_model, download_location)
            _dump_to_file(parsed_model, download_location, parsed_model['metadata']['uid'], MODEL_DIR)


def fetch_service_model(javascript_url):
    try:
        resp = requests.get(javascript_url, timeout=30)
    except Exception as e:
        logging.error(f"[!] Failed to retruenve {javascript_url} {e}")
        return None

    if resp.status_code != 200:
        logging.error(f"[!] Failed to retrieve {javascript_url}")
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
        model['metadata']['download_location'].append(download_location)

    for operation in model['operations']:
        if 'download_location' not in model['operations'][operation].keys():
            model['operations'][operation]['download_location'] = [download_location]
        elif download_location not in model['operations'][operation]['download_location']:
            model['operations'][operation]['download_location'].append(download_location)

    return model

        
def _uid_stored(uid, MODEL_DIR):
    for model_name in os.listdir(MODEL_DIR):
        if uid in model_name:
            return True
    return False


def _load_file(filename, MODEL_DIR):
    with open(f"{MODEL_DIR}/{filename}.json", "r") as r:
        return json.load(r)


def _get_models(uid, MODEL_DIR):
    to_return = []
    for model_name in os.listdir(MODEL_DIR):
        if uid in model_name:
            r = open(f"{MODEL_DIR}/{model_name}", "r")
            to_return.append( (model_name, json.load(r)) )
            r.close()
    return to_return


def _dump_to_file(model, download_location, filename, MODEL_DIR):
    filename = f"{MODEL_DIR}/{filename}.json"
    with open(filename, "w") as w:
        json.dump(model, w, indent=4)


def _integrate_models(parsed_model, existing_model, download_location):
    # First update existing ops
    for operation in existing_model['operations']:
        if operation in parsed_model['operations'].keys():
            existing_model['operations'][operation]['download_location'].append(download_location)

    # Next add new ones
    for operation in parsed_model['operations']:
        if operation not in existing_model['operations'].keys():
            logging.info(f"[+] Adding new operation: {existing_model['metadata']['uid']}:{operation}")
            existing_model['operations'][operation] = parsed_model['operations'][operation]
            if "download_location" not in existing_model['operations'][operation].keys():
                existing_model['operations'][operation]['download_location'] = [download_location]
            else:
                existing_model['operations'][operation]['download_location'].append(download_location)
    
    return existing_model
