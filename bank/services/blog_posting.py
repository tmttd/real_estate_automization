from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains, Keys
from .image_upload import get_map_images, get_ground_plan_images, select_random_images, upload_images_to_blog, get_specific_image
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import simpledialog
import time
import json
import os
import logging
import pyperclip
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import NoAlertPresentException
from typing import List
import keyboard

class NaverBlogPoster:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 3)
        self.actions = ActionChains(driver)

    def get_property_info(self, property_id):
        # MongoDB 연결 및 정보 조회
        client = MongoClient('mongodb://localhost:27017/')
        db = client['property_db']
        collections = db.list_collection_names()
        
        complex_name = None
        property_url = None
        
        for collection_name in collections:
            collection = db[collection_name]
            document = collection.find_one(
                {"매물목록": {"$elemMatch": {"매물번호": property_id}}},
                {"단지명": 1, "매물목록.$": 1}
            )
            
            if document:
                complex_name = document.get('단지명')
                if document.get('매물목록') and len(document['매물목록']) > 0:
                    property_url = document['매물목록'][0].get('URL')
                    print(f"단지명을 찾았습니다: {complex_name} (컬렉션: {collection_name})")
                    print(f"매물 URL: {property_url}")
                    break
        
        client.close()
        return complex_name, property_url

    def login(self, id, pwd):
        self.driver.get('https://blog.naver.com/juka103?Redirect=Write&')
        
        # 로그인
        id_input = self.driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/form/ul/li/div/div[1]/div/div[1]/input')
        id_input.click()
        pyperclip.copy(id)
        self.actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        time.sleep(1)
        
        pwd_input = self.driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/form/ul/li/div/div[1]/div/div[2]/input')
        pwd_input.click()
        pyperclip.copy(pwd)
        self.actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        time.sleep(1)
        
        button = self.driver.find_element(By.XPATH, '//*[@id="log.login"]')
        button.click()
        time.sleep(7)

    def write_post(self, title, information, description, complex_name, property_url):
        # iframe 전환
        self.driver.switch_to.frame('mainFrame')
        
        # 제목 작성
        title_element = self.wait.until(EC.presence_of_element_located((By.XPATH, '//span[contains(text(), "제목")]')))
        title_element.click()
        self.actions.send_keys(f"{title}").perform()
        
        # 본문 작성
        try:
            content_container = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.se-component.se-text.se-l-default'))
            )
            content_container.click()
            time.sleep(1)
            
            content_area = content_container.find_element(By.CSS_SELECTOR, 'p.se-text-paragraph')
            content_area.click()
            self.actions.send_keys(f'{information}').perform()
            time.sleep(2)
        except Exception as e:
            print("본문 영역을 찾을 수 없습니다:", str(e))

        # 이미지 업로드
        random_images = select_random_images(complex_name, num_images=3)
        upload_images_to_blog(self.driver, random_images)
        
        plan_images = get_ground_plan_images(complex_name)
        upload_images_to_blog(self.driver, plan_images)
        
        self.actions.send_keys(Keys.ESCAPE).perform()
        time.sleep(1)
        # 설명 추가
        self.actions.send_keys(f'{description}').perform()
        time.sleep(2)
        
        # 링크 추가
        self.actions.send_keys(Keys.ENTER).send_keys(Keys.ENTER).perform()
        self.actions.send_keys('-더 자세한 정보가 궁금하다면? 아래 링크 클릭!').perform()
        self.actions.send_keys(Keys.ENTER).perform()
        
        # URL 삽입
        # 링크 버튼 찾기 및 클릭
        link_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-name="oglink"]')
        self.driver.execute_script("arguments[0].click();", link_button)
        time.sleep(1)

        keyboard.press_and_release('tab')
        time.sleep(1)
        keyboard.press_and_release('tab')
        time.sleep(1)
        keyboard.press_and_release('tab')
        time.sleep(1)
        keyboard.press_and_release('enter')
        time.sleep(1)

        self.actions.send_keys(f'{property_url}').perform()
        time.sleep(1)
        self.actions.send_keys(Keys.ENTER).perform()
        # 확인 버튼이 클릭 가능할 때까지 대기 후 JavaScript로 클릭
        confirm_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.se-popup-button-confirm'))
        )
        # 버튼으로 스크롤
        self.driver.execute_script("arguments[0].scrollIntoView(true);", confirm_button)
        time.sleep(1)
        # 클릭 실행
        self.driver.execute_script("arguments[0].click();", confirm_button)
        time.sleep(1)
        
        # 추가 이미지
        image_path = get_specific_image(r"C:\Users\pqstv\Desktop\real_estate_automization\images\shop.jpg")
        upload_images_to_blog(self.driver, [image_path])
        
        image_path = get_specific_image(r"C:\Users\pqstv\Desktop\real_estate_automization\images\card.jpg")
        upload_images_to_blog(self.driver, [image_path])

        time.sleep(1)

    def publish_post(self):
        try:
            publish_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.publish_btn__m9KHH'))
            )
            self.driver.execute_script("arguments[0].click();", publish_button)
            time.sleep(1)

            category_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="root"]/div/div[1]/div/div[3]/div[2]/div/div/div/div[1]/div/div/button'))
            )
            self.driver.execute_script("arguments[0].click();", category_button)
            time.sleep(1)

            category_item = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'label[for="7_매물정보"]'))
            )
            self.driver.execute_script("arguments[0].click();", category_item)
            time.sleep(1)

            final_publish = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="root"]/div/div[1]/div/div[3]/div[2]/div/div/div/div[8]/div/button'))
            )
            self.driver.execute_script("arguments[0].click();", final_publish)
            time.sleep(2)
            return True

        except Exception as e:
            print("발행 과정에서 오류 발생:", str(e))
            return False