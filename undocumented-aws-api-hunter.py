#!/usr/bin/env python3
import os, datetime
import argparse, logging, sys

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

import selenium_driver
import aws_connector

MODEL_DIR = "./models"
LOG_DIR = "./logs"
ENDPOINTS_DIR = "./endpoints"


def main(args):
    # In case this is a single query
    if args.single:
        js_content = aws_connector.fetch_service_model(args.single)
        aws_connector.parse_service_model(js_content, args.single, True, MODEL_DIR)
        exit()

    driver = selenium_driver.create_driver(args)
    driver = selenium_driver.authenticate(driver)

    aws_services = aws_connector.fetch_services()

    endpoints = load_endpoints()

    for service in aws_services:
        queried_javascript = set()
        url = aws_connector.process_url(service)
        if url is None:
            continue

        driver.get(url)

        endpoints = endpoints.union(aws_connector.parse_endpoints(driver.page_source))
        javascript = aws_connector.find_javascript_urls(driver.page_source)
        for script in javascript:
            if script not in queried_javascript:
                js_content = aws_connector.fetch_service_model(script)
                if js_content is None:
                    continue

                aws_connector.parse_service_model(js_content, script, True, MODEL_DIR)
                queried_javascript.add(script)
    
    with open(f"{ENDPOINTS_DIR}/endpoints.txt", 'w') as w:
        for item in endpoints:
            w.write(f"{item}\n")


def load_endpoints():
    to_return = set()
    with open(f"{ENDPOINTS_DIR}/endpoints.txt", 'r') as r:
        for url in r:
            to_return.add(url.strip())
    return to_return


def initialize(args):
    # Check for a local models directory
    if not os.path.isdir(MODEL_DIR):
        os.mkdir(MODEL_DIR)
    #if not os.path.isdir("./incomplete"):
    #    os.mkdir("./incomplete")
    if not os.path.isdir(ENDPOINTS_DIR):
        os.mkdir(ENDPOINTS_DIR)
    if not os.path.isfile(f"{ENDPOINTS_DIR}/endpoints.txt"):
        open(f"{ENDPOINTS_DIR}/endpoints.txt", 'w').close()

    # Check needed environment variables
    env_vars = ["UAH_ACCOUNT_ID", "UAH_USERNAME", "UAH_PASSWORD"]
    for env_var in env_vars:
        # TODO: Fix this below
        if env_var not in os.environ:
            print(f"[!] Mising environment variable: {env_var}")
            print(f"[-] Terminating")
            exit()

    # Configure logging
    if not os.path.isdir(LOG_DIR):
        os.mkdir(LOG_DIR)

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            logging.FileHandler(f"{LOG_DIR}/application.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.getLogger('selenium').setLevel(logging.CRITICAL)
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    logging.getLogger('urllib3').setLevel(logging.CRITICAL)
    logging.getLogger('json').setLevel(logging.CRITICAL)
    logging.getLogger('chardet.charsetprober').setLevel(logging.CRITICAL)
    logging.getLogger('chardet.universaldetector').setLevel(logging.CRITICAL)

    timestamp = datetime.datetime.now() 
    logging.info(f"{datetime.datetime.now()} INFO - Starting new run at {timestamp.strftime('%m/%d/%Y %H:%M:%S')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find this pesky undocumented AWS APIs with the AWS Console")
    
    parser.add_argument('--headless', dest='headless', action='store_true', default=False,
                        help="Do not open a visible chrome window. Headless mode. (Default: False)")
    parser.add_argument('--single', dest='single', action='store', type=str,
                        help="Parses a single URL for its models.")

    args = parser.parse_args()

    initialize(args)

    main(args)
