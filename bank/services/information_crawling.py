from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .extract_and_save import check_property_type, process_property_info
from .download_images import download_images
import time
import random

class PropertyCrawler:
    def __init__(self, driver):
        self.driver = driver
        
        # WebDriverWait 객체 초기화
        self.wait = WebDriverWait(self.driver, 10)
        
        # MongoDB 클라이언트 초기화
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['property_db']
        
        # JavaScript 실행을 위한 코드 추가
        self.driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """)

    def login(self, user_id, password):
        """부동산 뱅크 로그인"""
        self.driver.get('https://www.neonet.co.kr/novo-rebank/view/member/MemberLogin.neo?login_check=yes&return_url=/novo-rebank/index.neo')
        
        id_input = self.driver.find_element(By.XPATH, '//*[@id="input_id"]')
        id_input.send_keys(user_id)
        pwd_input = self.driver.find_element(By.XPATH, '//*[@id="input_pw"]')
        pwd_input.send_keys(password)
        
        button = self.driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[1]/dl/dt/form/table[1]/tbody/tr[1]/td[2]/input')
        button.click()
        time.sleep(2)
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def navigate_to_property_list(self):
        """매물 관리 페이지로 이동"""
        try:
            # 매물관리 탭 클릭
            button_2 = self.driver.find_element(By.XPATH, '/html/body/div[3]/div[3]/div[1]/div/ul/li[2]/a')
            button_2.click()
            time.sleep(2)

            # 매물 목록이 로드될 때까지 대기
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "bbs_w"))
            )
            return True
            
        except Exception as e:
            print("매물 관리 페이지 접근 실패:", str(e))
            return False

    def crawl_property_info(self, property_id, save_path):
        """매물 정보 크롤링 실행"""
        try:
            # 매물 종류 확인
            check_property_type(self.driver, property_id)
            time.sleep(2)  # 매물 종류 확인 완료 대기
            
            # 데이터 크롤링
            process_property_info(self.driver, property_id)
            time.sleep(2)  # 데이터 크롤링 완료 대기
            
            # 이미지 다운로드
            download_images(self.driver, property_id, save_path)
            time.sleep(2)  # 이미지 다운로드 완료 대기
            
            return True
            
        except Exception as e:
            print(f"크롤링 중 오류 발생: {str(e)}")
            return False

    def print_complex_info(self):
        """단지 정보 출력"""
        print("\n=== 단지 정보 (apt) ===")
        apts = list(self.db.apt.find())
        for apt_data in apts:
            print("\n단지명:", apt_data['단지명'])
            
            print("\n이미지 목록:")
            for img in apt_data.get('이미지목록', []):
                print(f"- 카테고리: {img['카테고리']}")
                print(f"  저장경로: {img['저장경로']}")
            
            print("\n매물 목록:")
            for property in apt_data.get('매물목록', []):
                print(f"\n- 매물번호: {property['매물번호']}")
                print(f"  거래종류: {property.get('거래종류', 'N/A')}")
                print(f"  가격: {property.get('가격', 'N/A')}")
                print(f"  매물특징: {property.get('매물특징', 'N/A')}")
                print(f"  공급/전용면적: {property.get('공급/전용면적', 'N/A')}")
            print("="*50)

    def close(self):
        """브라우저 및 DB 연결 종료"""
        self.driver.quit()
        self.client.close()