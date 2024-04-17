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


def track_api_changes(config_file):
  """Tracks API changes based on user configuration and uses oasdiff for comparison.

  Args:
    config_file (str): Path to the configuration file containing API details.
  """

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

          shutil.move(f"openapi_{name}.json", old_spec_file)
        except FileNotFoundError:
          api_logger.info(f"No previous spec found for '{name}'. Using downloaded version as baseline.")
          shutil.copyfile(f"openapi_{name}.json", old_spec_file)  # Save downloaded spec as baseline
      else:
        api_logger.error(f"Failed to download spec for '{name}': Status code {response.status_code}")
    except Exception as e:
      api_logger.exception(f"An error occurred during download for '{name}':")


if __name__ == "__main__":
    current_dir = os.getcwd()
    print(f"Current working directory: {current_dir}")
    track_api_changes("config.json")
