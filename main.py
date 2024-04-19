import json
import os
import shutil
import subprocess
import logging
from venv import logger
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import smtplib
from dotenv import load_dotenv, dotenv_values 

load_dotenv() 

sender_email = os.getenv("SENDER_MAIL")
sender_password = os.getenv("SENDER_PASS")
recipient_email = os.getenv("RECIPIENT_MAIL")

def track_api_changes(config_file):
  with open(config_file, "r") as f:
    config = json.load(f)

  for api in config["apis"]:
    name = api["name"]
    url = api["url"]

    if not url:
      logger.error(f"API '{name}' is missing a URL in the configuration file.")
      continue

    api_logger = logging.getLogger(f"API.{name}")
    api_logger.setLevel(logging.INFO)

    try:
      response = requests.get(url)
      api_logger.error(f"Response '{response}'")
      if response.status_code == 200:
        with open(f"openapi_{name}.json", "wb") as f:
          f.write(response.content)
        api_logger.info(f"Download complete for '{name}'")

        old_spec_file = f"previous_{name}.json" 

        try:
          result = subprocess.run(["oasdiff", "breaking", f"openapi_{name}.json", old_spec_file], capture_output=True)
          if result.returncode != 0:
            api_logger.warning(f"API '{name}' might have breaking changes:")
            api_logger.debug(result.stdout.decode()) 
            send_email_notification(f"Breaking changes detected in API: {name}", result.stdout.decode())

          shutil.move(f"openapi_{name}.json", old_spec_file)
        except FileNotFoundError:
          api_logger.info(f"No previous spec found for '{name}'. Using downloaded version as baseline.")
          shutil.copyfile(f"openapi_{name}.json", old_spec_file)
      else:
        api_logger.error(f"Failed to download spec for '{name}': Status code {response.status_code}")
    except Exception as e:
      api_logger.exception(f"An error occurred during download for '{name}':")


def send_email_notification(subject, message):
  try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    msg = f"Subject: {subject}\n\n{message}"
    server.sendmail(sender_email, recipient_email, msg)
    server.quit()
    print(f"Email notification sent for API: {subject}")
  except Exception as e:
    print(f"Error sending email notification: {e}")

if __name__ == "__main__":
    current_dir = os.getcwd()
    track_api_changes("config.json")
