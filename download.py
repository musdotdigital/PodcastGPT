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

CHROME_DRIVER_PATH = '/chromedriver_mac_arm64'


def generate_filename_from_url(url: str) -> str:
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    return unquote(filename)


def download_mp3(url: str, destination: str = "downloaded-pod.mp3"):
    response = requests.get(url)
    with open(destination, "w") as f:
        f.write(response.content)
    print(f"Podcast MP3 downloaded as {destination}")


def get_mp3_url(apple_url):
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
        play_button.click()
        time.sleep(2)  # Wait for audio element to load

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        audio_tag = soup.find('audio', {'id': 'apple-music-player'})

        if audio_tag:
            return audio_tag.get('src')
        else:
            return None
    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(
        description="Extract MP3 URL from Apple Podcast URL")
    parser.add_argument("url", help="Apple Podcast URL")
    args = parser.parse_args()

    mp3_url = get_mp3_url(args.url)
    if mp3_url:
        gen_mp3 = generate_filename_from_url(mp3_url)
        print(f"MP3 URL: {gen_mp3}")
        download_mp3(mp3_url)
    else:
        print("Could not find the MP3 URL for the given Apple Podcast URL.")


if __name__ == "__main__":
    main()
