import requests
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import shutil
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name)

url = "https://dev.bandwidth.com/apis/messaging/"

service = Service(executable_path=r'/usr/bin/chromedriver')
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=service, options=options)

driver.get(url)

try:
    wait = WebDriverWait(driver, 10) 
    #download_link = driver.find_element(By.CSS_SELECTOR, '.sc-ktJbId')
    download_link = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Download")))
    
    if download_link:
        file_url = download_link.get_attribute("href")
        
        with requests.get(file_url, stream=True) as file_response:
            with open("openapi.json", "wb") as f:
                shutil.copyfileobj(file_response.raw, f)
            
        logger.info("Download complete!")
    else:
        logger.error("Download link not found.")
except Exception as e:
    logger.exception("An error occurred during download:")
finally:
    driver.quit()