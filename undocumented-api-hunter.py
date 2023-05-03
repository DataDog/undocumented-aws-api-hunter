#!/usr/bin/env python3
import requests, re, json, os, time, datetime
import argparse, logging, sys

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from sqlalchemy import create_engine

from db_models import Model, Operation

import selenium_driver
import aws_connector
import database

MODEL_DIR = "./models"
LOG_DIR = "./logs"


def main(args):
    # In case this is a single query
    if args.single:
        js_content = aws_connector.fetch_service_model(args.single)
        aws_connector.parse_service_model(js_content, args.single, True, MODEL_DIR)
        exit()
    elif args.dcount:
        print(args.dcount)
        exit()
    elif args.extract:
        js_content = aws_connector.fetch_service_model(args.extract)
        aws_connector.parse_service_model(js_content, args.extract, False, MODEL_DIR)
        exit()
    elif args.manual:
        database.manual_db_load(MODEL_DIR)
        exit()

    driver = selenium_driver.create_driver(args)
    driver = selenium_driver.authenticate(driver)

    aws_services = aws_connector.fetch_services()

    queried_javascript = set()
    endpoints = set()

    for service in aws_services:
        url = aws_connector.process_url(service)
        if url is None:
            continue

        driver.get(url)

        endpoints = aws_connector.add_endpoints(driver.page_source, endpoints)
        javascript = aws_connector.find_javascript(driver.page_source)
        for script in javascript:
            if script not in queried_javascript:
                js_content = aws_connector.fetch_service_model(script)
                if js_content is None:
                    continue

                aws_connector.parse_service_model(js_content, script, True, MODEL_DIR)
                queried_javascript.add(script)
    
    with open("./endpoints.txt", 'w') as w:
        for item in endpoints:
            w.write(f"{item}\n")


def uid_stored(uid):
    for definition in os.listdir("./crawled"):
        if uid in definition:
            return True
    return False


def mark_download_location(parsed, download_location):
    parsed['metadata']['download_location'] = [download_location]
    for operation in parsed['operations']:
        parsed['operations'][operation]['download_location'] = [download_location]
    return parsed


def initialize(args):
    # Check for a local models directory
    if not os.path.isdir(MODEL_DIR):
        os.mkdir(MODEL_DIR)

    # Check needed environment variables
    env_vars = ["UAH_ACCOUNT_ID", "UAH_USERNAME", "UAH_PASSWORD"]
    for env_var in env_vars:
        # TODO: Fix this below
        if env_var not in os.environ and not args.manual:
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
    logging.getLogger('sqlalchemy.engine').setLevel(logging.CRITICAL)

    timestamp = datetime.datetime.now() 
    logging.info(f"{datetime.datetime.now()} INFO - Starting new run at {timestamp.strftime('%m/%d/%Y %H:%M:%S')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find this pesky undocumented AWS APIs with the AWS Console")
    
    parser.add_argument('--headless', dest='headless', action='store_true', default=False,
                        help="Do not open a visible chrome window. Headless mode. (Default: False)")
    parser.add_argument('--single', dest='single', action='store', type=str,
                        help="Parses a single URL for its models.")
    parser.add_argument('--dcount', dest='dcount', action='store', type=int,
                        help="Displays all operations for a model with x number of download locations")
    parser.add_argument('--extract', dest='extract', action='store', type=str,
                        help="Extract all service models from a given URL.")
    parser.add_argument('--manual-load', dest='manual', action='store_true', default=False,
                        help="Manually load models into the DB.")

    args = parser.parse_args()

    initialize(args)

    main(args)
