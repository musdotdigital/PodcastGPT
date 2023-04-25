import argparse
import time
import requests
import os
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

CHROME_DRIVER_PATH = ""

for file in os.listdir("."):
    if file.startswith("chromedriver"):
        CHROME_DRIVER_PATH = os.path.join(os.getcwd(), file)
        break

if not os.path.exists(CHROME_DRIVER_PATH):
    print("Chrome driver not found. Please download the driver from https://chromedriver.chromium.org/downloads and place it in the root directory of this project.")


# turn 'Hello World' into 'Hello_World.mp3'
def strip_title(title):
    return title.replace(' ', '_').replace("'", '') + '.mp3'


def download_podcast(url: str, filename: str):
    response = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(response.content)


def get_podcast_details(apple_url):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    chrome_service = Service(executable_path=CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=chrome_service, options=options)

    driver.get(apple_url)
    try:

        play_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[contains(@class, "product-controls__button")]'))
        )

        podcast_title = driver.find_element(
            By.XPATH, '//span[contains(@class, "product-header__title")]')

        play_button.click()
        time.sleep(2)  # Wait for audio element to load

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        audio_tag = soup.find('audio', {'id': 'apple-music-player'})

        if audio_tag and podcast_title:
            return audio_tag.get('src'), strip_title(podcast_title.text)
        else:
            print('')
            return None

    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', "--url", type=str, required=True)

    args = parser.parse_args()

    podcast_url, file_name = get_podcast_details(args.url)

    if not podcast_url:
        print("Could not find the MP3 URL for the given Apple Podcast URL.")
        return

    if not file_name:
        print("Could not find podcast name for the given Apple Podcast URL. Using default name podcast.mp3...")
        file_name = 'podcast.mp3'

    print('Downloading file at ' + file_name)
    download_podcast(podcast_url, file_name)


if __name__ == "__main__":
    main()
