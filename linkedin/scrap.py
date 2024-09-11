from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv
import os
import pandas as pd
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import requests

# Çevresel değişkenleri yükle
load_dotenv()

chrome_options = Options()
  # Headless mode  # Bazı sistemlerde gereklidir

service = Service()
# WebDriver'ı başlatıyoruz
driver = webdriver.Chrome(service=service, options=chrome_options)

def login():
    linkedin_username = os.getenv('LINKEDIN_USERNAME')
    linkedin_password = os.getenv('LINKEDIN_PASSWORD')

    driver.get('https://www.linkedin.com/login')

    # Kullanıcı adı ve şifre alanlarını buluyoruz ve dolduruyoruz.
    username_field = driver.find_element(By.ID, 'username')
    username_field.send_keys(linkedin_username)

    password_field = driver.find_element(By.ID, 'password')
    password_field.send_keys(linkedin_password)

    # Giriş yap butonuna tıklıyoruz.
    login_button = driver.find_element(By.XPATH, '//*[@type="submit"]')
    login_button.click()

    # Giriş yapıldıktan sonra sayfanın yüklenmesini beklemek için kısa bir bekleme süresi.
    time.sleep(10)

def main(search_query, page_no):
    driver.get(f'https://www.linkedin.com/search/results/people/?keywords={search_query}&origin=SWITCH_SEARCH_VERTICAL&page={page_no}&sid=4hg')

    # Sayfanın tam olarak yüklenmesi için bir süre bekliyoruz.
    time.sleep(1)

    src = driver.page_source
    soup = BeautifulSoup(src, 'html.parser')

    return profile_scrap(soup)

def profile_scrap(soup):
    print("START PROFILE SCRAP")
    profiles_data = []

    # Profil kartlarını bulma
    profiles = soup.find_all('div', class_='display-flex align-items-center')

    for profile in profiles:
        # Profil linkini al
        profile_link_tag = profile.find('a', class_='app-aware-link')
        profile_link = profile_link_tag['href'] if profile_link_tag else 'Profil Link Bulunamadı'

        # Profil resim URL'sini al
        img_tag = profile.find('img', class_='presence-entity__image')
        image_url = img_tag['src'] if img_tag else 'null'

        # Profil ismini al
        name_tag = profile.find('img', class_='presence-entity__image')
        name = name_tag['alt'] if name_tag else 'İsim Bulunamadı'

        if image_url != 'null':
            profiles_data.append({
                'Profile Link': profile_link,
                'Image URL': image_url,
                'Name': name
            })

    return profiles_data

def img_download(df):
    # DataFrame'deki ilk sütundaki linkleri listeye alın
    urls = df['Image URL'].tolist()

    # Resimlerin kaydedileceği klasör
    save_folder = 'data'

    # Klasörün var olup olmadığını kontrol et ve oluştur
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # Her bir link için resimleri indirin
    for index, url in enumerate(urls):
        try:
            # Resmi indir
            response = requests.get(url)
            response.raise_for_status()  # Hata varsa istisna fırlat
            # Dosya adını oluştur
            file_name = os.path.join(save_folder, f'{index}.jpg')
            # Resmi kaydet
            with open(file_name, 'wb') as file:
                file.write(response.content)
            print(f'Resim {file_name} olarak kaydedildi.')
        except requests.exceptions.RequestException as e:
            print(f'Bir hata oluştu: {e}')

def close_driver():
    driver.quit()  # WebDriver'ı kapatır ve tarayıcıyı kapatır
