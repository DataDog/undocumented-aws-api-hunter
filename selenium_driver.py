import os, time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER

def create_driver(args):
    chrome_options = webdriver.ChromeOptions()
    if args.headless:
        chrome_options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def authenticate(driver):
    UAH_ACCOUNT_ID = os.getenv("UAH_ACCOUNT_ID")
    UAH_USERNAME = os.getenv("UAH_USERNAME")
    UAH_PASSWORD = os.getenv("UAH_PASSWORD")
    driver.get("https://us-east-1.console.aws.amazon.com/console/home?region=us-east-1")
    driver.find_element(By.ID, "iam_user_radio_button").click()
    time.sleep(1)
    driver.find_element(By.ID, "resolving_input").send_keys(UAH_ACCOUNT_ID)
    time.sleep(1)
    driver.find_element(By.ID, "resolving_input").send_keys(Keys.RETURN)
    time.sleep(1)
    driver.find_element(By.ID, "username").send_keys(UAH_USERNAME)
    time.sleep(1)
    driver.find_element(By.ID, "password").send_keys(UAH_PASSWORD)
    time.sleep(1)
    driver.find_element(By.ID, "password").send_keys(Keys.RETURN)
    time.sleep(3)
    return driver