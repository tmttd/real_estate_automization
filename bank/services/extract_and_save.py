from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import time
import json
import os
import logging
import requests
from urllib.parse import urlparse

# MongoDB 연결 설정
client = MongoClient('mongodb://localhost:27017/')
db = client['property_db']

def select_property(driver, property_id):
    """특정 매물의 수정 버튼 클릭"""
    try:
        if not property_id:
            raise ValueError("매물번호를 입력하세요.")
        
        # 수정 버튼 찾아서 클릭
        modify_button = driver.find_element(
            By.XPATH, 
            f"//tr[contains(.//a, '{property_id}')]//a[contains(@href, 'goModify')]"
        )
        modify_button.click()
        time.sleep(2)
        
        # 새 창으로 전환
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(2)
        return True
        
    except Exception as e:
        print("매물 수정 버튼 클릭 실패:", str(e))
        return False


# 아파트, 재건축, 주상복합인 경우
def extract_and_save_apt(driver, property_id):
    try:
        # 1단계: 매물 목록 페이지에서 정보 추출
        property_data = {
            "생성일자": datetime.now(),
            "매물번호": property_id,
        }
        
        # 매물 목록 페이지에서 필요한 정보 추출
                # 매물 목록 페이지에서 해당 매물 행 찾기
        row = driver.find_element(By.XPATH, f"//tr[contains(.//a, '{property_id}')]")
        
        # 필요한 정보 추출
        property_data.update({
            "거래종류": row.find_element(By.XPATH, "./td[3]").text.strip(),
            "매물종류": row.find_element(By.XPATH, "./td[4]").text.strip(),
            "소재지": row.find_element(By.XPATH, "./td[5]").text.strip(),
            "단지명": row.find_element(By.XPATH, "./td[6]").text.strip(),
            "세부단지명": row.find_element(By.XPATH, "./td[7]").text.strip(),
            "면적": '/'.join(area + "㎡" for area in row.find_element(By.XPATH, "./td[8]").text.strip().split('\n')),
            "가격": row.find_element(By.XPATH, "./td[9]").text.strip(),
        })
        
        # 2단계: 매물 상세 페이지로 이동
        select_property(driver, property_id)
        
        # 3단계: 매물 상세 페이지에서 정보 추출
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        # 상세 필드 정보 추출
        property_fields = {
            "해당층/총층": "해당층/총층", 
            "방향": "방향",
            "현관구조": "현관구조",
            "방수": "방수",
            "총세대수": "총세대수",
            "욕실수": "욕실수",
            "입주가능일": "입주가능일",
            "총 주차대수": "총 주차대수",
            "세대당 주차대수": "세대당 주차대수",
            "해당면적세대수": "해당면적세대수",
            "건축물용도": "건축물용도",
            "매물특징": "매물특징",
            "상세설명": "상세설명"
        }

        for key, field in property_fields.items():
            try:
                # 모든 th 태그를 찾아서 해당 필드가 포함된 것을 찾기
                for th in soup.find_all('th'):
                    if field in th.text:
                        td = th.find_next('td')
                        
                        # 입주가능일 특별 처리
                        if field == "입주가능일":
                            # 즉시입주 체크 여부 확인
                            if td.find('input', {'id': 'move_gbn_A', 'checked': True}):
                                field_value = "즉시입주"
                            #  날짜 선택 확인
                            else:
                                year = td.find('select', {'id': 'move_year'}).find('option', selected=True)
                                month = td.find('select', {'id': 'move_month'}).find('option', selected=True)
                                day = td.find('select', {'id': 'move_day'}).find('option', selected=True)
                                
                                if year and month and day:
                                    field_value = f"{year.text}/{month.text}/{day.text}이후"
                                    
                            # 협의가능 체크 여부 확인
                            if td.find('input', {'id': 'is_move_consult', 'checked': True}):
                                field_value = f"{field_value}(협의가능)" if field_value else "협의가능"
                        
                        # textarea 태그 확인
                        elif td.find('textarea'):
                            field_value = td.find('textarea').text.strip()
                        
                        # input 태그 확인
                        elif td.find('input', {'class': 'input'}):
                            input_tag = td.find('input', {'class': 'input'})
                            if input_tag.get('value'):
                                field_value = input_tag.get('value').strip()
                        
                        # select 태그 확인
                        elif td.find('select'):
                            selected_option = td.find('select').find('option', selected=True)
                            field_value = selected_option.text.strip() if selected_option else None
                        
                        # 모두 해당 없는 경우 일반 텍스트
                        else:
                            field_value = td.get_text(strip=True)
                            
                        property_data[key] = field_value
                        print(f"[크롤링 데이터] {key}: {field_value}")
                        break
                        
            except Exception as e:
                print(f"[크롤링 실패] {field} 정보 추출 실패: {str(e)}")
                property_data[key] = None

        # 전체 데이터 출력
        print("\n=== 전체 크롤링 데이터 ===")
        for key, value in property_data.items():
            print(f"{key}: {value}")
        print("========================\n")
        
        # 모든 데이터 수집 후
        if '해당층/총층' in property_data:
            floors = property_data['해당층/총층'].replace('\n', '').replace(' ', '').replace('\xa0', '').split('/')
            floors = [f.strip() for f in floors if f.strip()]
            if len(floors) == 2:
                property_data['해당층/총층'] = f"{floors[0]}/{floors[1]}"

        # 4단계: DB 저장
        try:
            complex_name = property_data['단지명']
            apt_collection = db['apt']
            
            # property_data에서 단지명 제거 (복사본 생성)
            property_data_to_save = property_data.copy()
            property_data_to_save.pop('단지명')
            
            existing_complex = apt_collection.find_one({
                "단지명": complex_name,
                "매물목록.매물번호": property_id
            })
            
            if existing_complex:
                result = apt_collection.update_one(
                    {
                        "단지명": complex_name,
                        "매물목록.매물번호": property_id
                    },
                    {"$set": {"매물목록.$": property_data_to_save}}
                )
                print(f"기존 매물 정보 업데이트: {complex_name} - {property_id}")
            else:
                result = apt_collection.update_one(
                    {"단지명": complex_name},
                    {
                        "$push": {"매물목록": property_data_to_save},
                        "$setOnInsert": {"이미지목록": []}
                    },
                    upsert=True
                )
                print(f"새로운 매물 추가: {complex_name} - {property_id}")
            
        except Exception as e:
            print(f"매물 정보 저장 중 오류 발생: {str(e)}")
    except Exception as e:
        print(f"매물 크롤링 중 오류 발생: {str(e)}")
    
    driver.back()
    
# 상가인 경우
def extract_and_save_market(driver, property_id):
    try:
        # 1단계: 매물 목록 페이지에서 정보 추출
        property_data = {
            "생성일자": datetime.now(),
            "매물번호": property_id,
        }
        
        # 매물 목록 페이지에서 필요한 정보 추출
        # 매물 목록 페이지에서 해당 매물 행 찾기
        row = driver.find_element(By.XPATH, f"//tr[contains(.//a, '{property_id}')]")
        
        # 필요한 정보 추출
        property_data.update({
            "거래종류": row.find_element(By.XPATH, "./td[3]").text.strip(),
            "매물종류": row.find_element(By.XPATH, "./td[4]").text.strip(),
            "소재지": row.find_element(By.XPATH, "./td[5]").text.strip(),
            "세부단지명": row.find_element(By.XPATH, "./td[7]").text.strip(),
            "면적": '/'.join(area + "㎡" for area in row.find_element(By.XPATH, "./td[8]").text.strip().split('\n')),
            "가격": row.find_element(By.XPATH, "./td[9]").text.strip(),
        })
        
        # 2단계: 매물 상세 페이지로 이동
        # property_id 링크 클릭
        property_link = driver.find_element(By.XPATH, f"//a[@href=\"javascript:goDetail('{property_id}', 'RB', 'A');\"]")
        property_link.click()
        
        # 3단계: 매물 상세 페이지에서 정보 추출
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        # 상세 필드 정보 추출
        property_fields = {
            "단지명": "상가명",
            "건물종류": "건물종류",
            "건축물용도": "건축물용도",
            "권리금": "권리금",
            "월 관리비": "월 관리비",
            "해당층/총층": "해당층/총층", 
            "방향": "방향",
            "현관구조": "현관구조",
            "방수": "방수",
            "총세대수": "총세대수",
            "욕실수": "욕실수",
            "입주가능일": "입주가능일",
            "총 주차대수": "총 주차대수",
            "건축물용도": "건축물용도",
            "매물특징": "매물특징",
            "상세설명": "상세설명"
        }

        for key, field in property_fields.items():
            try:
                # 모든 th 태그를 찾아서 해당 필드가 포함된 것을 찾기
                for th in soup.find_all('th'):
                    if field in th.text:
                        td = th.find_next('td')
                        field_value = None
                        
                        # textarea 태그 확인
                        if td.find('textarea'):
                            field_value = td.find('textarea').text.strip()
                        
                        # input 태그 확인
                        elif td.find('input', {'class': 'input'}):
                            input_tag = td.find('input', {'class': 'input'})
                            if input_tag.get('value'):
                                field_value = input_tag.get('value').strip()
                        
                        # select 태그 확인
                        elif td.find('select'):
                            selected_option = td.find('select').find('option', selected=True)
                            field_value = selected_option.text.strip() if selected_option else None
                        
                        # 모두 해당 없는 경우 일반 텍스트
                        else:
                            field_value = td.get_text(strip=True)
                            
                        property_data[key] = field_value
                        print(f"[크롤링 데이터] {key}: {field_value}")
                        break
                        
            except Exception as e:
                print(f"[크롤링 실패] {field} 정보 추출 실패: {str(e)}")
                property_data[key] = None

        # 전체 데이터 출력
        print("\n=== 전체 크롤링 데이터 ===")
        for key, value in property_data.items():
            print(f"{key}: {value}")
        print("========================\n")
        
        # 모든 데이터 수집 후
        if '해당층/총층' in property_data:
            floors = property_data['해당층/총층'].replace('\n', '').replace(' ', '').replace('\xa0', '').split('/')
            floors = [f.strip() for f in floors if f.strip()]
            if len(floors) == 2:
                property_data['해당층/총층'] = f"{floors[0]}/{floors[1]}"

        # 4단계: DB 저장
        try:
            complex_name = property_data['단지명']
            apt_collection = db['apt']
            
            # property_data에서 단지명 제거 (복사본 생성)
            property_data_to_save = property_data.copy()
            property_data_to_save.pop('단지명')
            
            existing_complex = apt_collection.find_one({
                "단지명": complex_name,
                "매물목록.매물번호": property_id
            })
            
            if existing_complex:
                result = apt_collection.update_one(
                    {
                        "단지명": complex_name,
                        "매물목록.매물번호": property_id
                    },
                    {"$set": {"매물목록.$": property_data_to_save}}
                )
                print(f"기존 매물 정보 업데이트: {complex_name} - {property_id}")
            else:
                result = apt_collection.update_one(
                    {"단지명": complex_name},
                    {
                        "$push": {"매물목록": property_data_to_save},
                        "$setOnInsert": {"이미지목록": []}
                    },
                    upsert=True
                )
                print(f"새로운 매물 추가: {complex_name} - {property_id}")
            
        except Exception as e:
            print(f"매물 정보 저장 중 오류 발생: {str(e)}")
    except Exception as e:
        print(f"매물 크롤링 중 오류 발생: {str(e)}")

    driver.back()

# 빌라, 단독/다가구 인 경우
def extract_and_save_villa(driver, property_id):
    try:
        # 1단계: 매물 목록 페이지에서 정보 추출
        property_data = {
            "생성일자": datetime.now(),
            "매물번호": property_id,
        }
        
        # 매물 목록 페이지에서 필요한 정보 추출
                # 매물 목록 페이지에서 해당 매물 행 찾기
        row = driver.find_element(By.XPATH, f"//tr[contains(.//a, '{property_id}')]")
        
        # 필요한 정보 추출
        property_data.update({
            "거래종류": row.find_element(By.XPATH, "./td[3]").text.strip(),
            "매물종류": row.find_element(By.XPATH, "./td[4]").text.strip(),
            "소재지": row.find_element(By.XPATH, "./td[5]").text.strip(),
            "단지명": row.find_element(By.XPATH, "./td[6]").text.strip(),
            "세부단지명": row.find_element(By.XPATH, "./td[7]").text.strip(),
            "면적": '/'.join(area + "㎡" for area in row.find_element(By.XPATH, "./td[8]").text.strip().split('\n')),
            "가격": row.find_element(By.XPATH, "./td[9]").text.strip(),
        })
        
        # 2단계: 매물 상세 페이지로 이동
        select_property(driver, property_id)
        
        # 3단계: 매물 상세 페이지에서 정보 추출
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        # 상세 필드 정보 추출
        property_fields = {
            "해당층/총층": "해당층/총층", 
            "방향": "방향",
            "현관구조": "현관구조",
            "방수": "방수",
            "총세대수": "총세대수",
            "욕실수": "욕실수",
            "입주가능일": "입주가능일",
            "총 주차대수": "총 주차대수",
            "세대당 주차대수": "세대당 주차대수",
            "해당면적세대수": "해당면적세대수",
            "건축물용도": "건축물용도",
            "매물특징": "매물특징",
            "상세설명": "상세설명"
        }

        for key, field in property_fields.items():
            try:
                # 모든 th 태그를 찾아서 해당 필드가 포함된 것을 찾기
                for th in soup.find_all('th'):
                    if field in th.text:
                        td = th.find_next('td')
                        
                        # 입주가능일 특별 처리
                        if field == "입주가능일":
                            # 즉시입주 체크 여부 확인
                            if td.find('input', {'id': 'move_gbn_A', 'checked': True}):
                                field_value = "즉시입주"
                            #  날짜 선택 확인
                            else:
                                year = td.find('select', {'id': 'move_year'}).find('option', selected=True)
                                month = td.find('select', {'id': 'move_month'}).find('option', selected=True)
                                day = td.find('select', {'id': 'move_day'}).find('option', selected=True)
                                
                                if year and month and day:
                                    field_value = f"{year.text}/{month.text}/{day.text}이후"
                                    
                            # 협의가능 체크 여부 확인
                            if td.find('input', {'id': 'is_move_consult', 'checked': True}):
                                field_value = f"{field_value}(협의가능)" if field_value else "협의가능"
                        
                        # textarea 태그 확인
                        elif td.find('textarea'):
                            field_value = td.find('textarea').text.strip()
                        
                        # input 태그 확인
                        elif td.find('input', {'class': 'input'}):
                            input_tag = td.find('input', {'class': 'input'})
                            if input_tag.get('value'):
                                field_value = input_tag.get('value').strip()
                        
                        # select 태그 확인
                        elif td.find('select'):
                            selected_option = td.find('select').find('option', selected=True)
                            field_value = selected_option.text.strip() if selected_option else None
                        
                        # 모두 해당 없는 경우 일반 텍스트
                        else:
                            field_value = td.get_text(strip=True)
                            
                        property_data[key] = field_value
                        print(f"[크롤링 데이터] {key}: {field_value}")
                        break
                        
            except Exception as e:
                print(f"[크롤링 실패] {field} 정보 추출 실패: {str(e)}")
                property_data[key] = None

        # 전체 데이터 출력
        print("\n=== 전체 크롤링 데이터 ===")
        for key, value in property_data.items():
            print(f"{key}: {value}")
        print("========================\n")
        
        # 모든 데이터 수집 후
        if '해당층/총층' in property_data:
            floors = property_data['해당층/총층'].replace('\n', '').replace(' ', '').replace('\xa0', '').split('/')
            floors = [f.strip() for f in floors if f.strip()]
            if len(floors) == 2:
                property_data['해당층/총층'] = f"{floors[0]}/{floors[1]}"

        # 4단계: DB 저장
        try:
            complex_name = property_data['단지명']
            apt_collection = db['apt']
            
            # property_data에서 단지명 제거 (복사본 생성)
            property_data_to_save = property_data.copy()
            property_data_to_save.pop('단지명')
            
            existing_complex = apt_collection.find_one({
                "단지명": complex_name,
                "매물목록.매물번호": property_id
            })
            
            if existing_complex:
                result = apt_collection.update_one(
                    {
                        "단지명": complex_name,
                        "매물목록.매물번호": property_id
                    },
                    {"$set": {"매물목록.$": property_data_to_save}}
                )
                print(f"기존 매물 정보 업데이트: {complex_name} - {property_id}")
            else:
                result = apt_collection.update_one(
                    {"단지명": complex_name},
                    {
                        "$push": {"매물목록": property_data_to_save},
                        "$setOnInsert": {"이미지목록": []}
                    },
                    upsert=True
                )
                print(f"새로운 매물 추가: {complex_name} - {property_id}")
            
        except Exception as e:
            print(f"매물 정보 저장 중 오류 발생: {str(e)}")
    except Exception as e:
        print(f"매물 크롤링 중 오류 발생: {str(e)}")
    
    driver.back()
    
# 오피스텔인 경우
def extract_and_save_officetel(driver, property_id):
    try:
        # 1단계: 매물 목록 페이지에서 정보 추출
        property_data = {
            "생성일자": datetime.now(),
            "매물번호": property_id,
        }
        
        # 매물 목록 페이지에서 필요한 정보 추출
                # 매물 목록 페이지에서 해당 매물 행 찾기
        row = driver.find_element(By.XPATH, f"//tr[contains(.//a, '{property_id}')]")
        
        # 필요한 정보 추출
        property_data.update({
            "거래종류": row.find_element(By.XPATH, "./td[3]").text.strip(),
            "매물종류": row.find_element(By.XPATH, "./td[4]").text.strip(),
            "소재지": row.find_element(By.XPATH, "./td[5]").text.strip(),
            "단지명": row.find_element(By.XPATH, "./td[6]").text.strip(),
            "세부단지명": row.find_element(By.XPATH, "./td[7]").text.strip(),
            "면적": '/'.join(area + "㎡" for area in row.find_element(By.XPATH, "./td[8]").text.strip().split('\n')),
            "가격": row.find_element(By.XPATH, "./td[9]").text.strip(),
        })
        
        # 2단계: 매물 상세 페이지로 이동
        select_property(driver,property_id)
        
        # 3단계: 매물 상세 페이지에서 정보 추출
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        # 상세 필드 정보 추출
        property_fields = {
            "해당층/총층": "해당층/총층", 
            "방향": "방향",
            "현관구조": "현관구조",
            "방수": "방수",
            "총세대수": "총세대수",
            "욕실수": "욕실수",
            "입주가능일": "입주가능일",
            "총 주차대수": "총 주차대수",
            "세대당 주차대수": "세대당 주차대수",
            "해당면적세대수": "해당면적세대수",
            "건축물용도": "건축물용도",
            "매물특징": "매물특징",
            "상세설명": "상세설명"
        }

        for key, field in property_fields.items():
            try:
                # 모든 th 태그를 찾아서 해당 필드가 포함된 것을 찾기
                for th in soup.find_all('th'):
                    if field in th.text:
                        td = th.find_next('td')
                        
                        # 입주가능일 특별 처리
                        if field == "입주가능일":
                            # 즉시입주 체크 여부 확인
                            if td.find('input', {'id': 'move_gbn_A', 'checked': True}):
                                field_value = "즉시입주"
                            #  날짜 선택 확인
                            else:
                                year = td.find('select', {'id': 'move_year'}).find('option', selected=True)
                                month = td.find('select', {'id': 'move_month'}).find('option', selected=True)
                                day = td.find('select', {'id': 'move_day'}).find('option', selected=True)
                                
                                if year and month and day:
                                    field_value = f"{year.text}/{month.text}/{day.text}이후"
                                    
                            # 협의가능 체크 여부 확인
                            if td.find('input', {'id': 'is_move_consult', 'checked': True}):
                                field_value = f"{field_value}(협의가능)" if field_value else "협의가능"
                        
                        # textarea 태그 확인
                        elif td.find('textarea'):
                            field_value = td.find('textarea').text.strip()
                        
                        # input 태그 확인
                        elif td.find('input', {'class': 'input'}):
                            input_tag = td.find('input', {'class': 'input'})
                            if input_tag.get('value'):
                                field_value = input_tag.get('value').strip()
                        
                        # select 태그 확인
                        elif td.find('select'):
                            selected_option = td.find('select').find('option', selected=True)
                            field_value = selected_option.text.strip() if selected_option else None
                        
                        # 모두 해당 없는 경우 일반 텍스트
                        else:
                            field_value = td.get_text(strip=True)
                            
                        property_data[key] = field_value
                        print(f"[크롤링 데이터] {key}: {field_value}")
                        break
                        
            except Exception as e:
                print(f"[크롤링 실패] {field} 정보 추출 실패: {str(e)}")
                property_data[key] = None

        # 전체 데이터 출력
        print("\n=== 전체 크롤링 데이터 ===")
        for key, value in property_data.items():
            print(f"{key}: {value}")
        print("========================\n")
        
        # 모든 데이터 수집 후
        if '해당층/총층' in property_data:
            floors = property_data['해당층/총층'].replace('\n', '').replace(' ', '').replace('\xa0', '').split('/')
            floors = [f.strip() for f in floors if f.strip()]
            if len(floors) == 2:
                property_data['해당층/총층'] = f"{floors[0]}/{floors[1]}"

        # 4단계: DB 저장
        try:
            complex_name = property_data['단지명']
            apt_collection = db['apt']
            
            # property_data에서 단지명 제거 (복사본 생성)
            property_data_to_save = property_data.copy()
            property_data_to_save.pop('단지명')
            
            existing_complex = apt_collection.find_one({
                "단지명": complex_name,
                "매물목록.매물번호": property_id
            })
            
            if existing_complex:
                result = apt_collection.update_one(
                    {
                        "단지명": complex_name,
                        "매물목록.매물번호": property_id
                    },
                    {"$set": {"매물목록.$": property_data_to_save}}
                )
                print(f"기존 매물 정보 업데이트: {complex_name} - {property_id}")
            else:
                result = apt_collection.update_one(
                    {"단지명": complex_name},
                    {
                        "$push": {"매물목록": property_data_to_save},
                        "$setOnInsert": {"이미지목록": []}
                    },
                    upsert=True
                )
                print(f"새로운 매물 추가: {complex_name} - {property_id}")
            
        except Exception as e:
            print(f"매물 정보 저장 중 오류 발생: {str(e)}")
    except Exception as e:
        print(f"매물 크롤링 중 오류 발생: {str(e)}")
        
    driver.back()
    
# 사무실인 경우
def extract_and_save_office(driver, property_id):
    try:
        # 1단계: 매물 목록 페이지에서 정보 추출
        property_data = {
            "생성일자": datetime.now(),
            "매물번호": property_id,
        }
        
        # 매물 목록 페이지에서 필요한 정보 추출
        # 매물 목록 페이지에서 해당 매물 행 찾기
        row = driver.find_element(By.XPATH, f"//tr[contains(.//a, '{property_id}')]")
        
        # 필요한 정보 추출
        property_data.update({
            "거래종류": row.find_element(By.XPATH, "./td[3]").text.strip(),
            "매물종류": row.find_element(By.XPATH, "./td[4]").text.strip(),
            "소재지": row.find_element(By.XPATH, "./td[5]").text.strip(),
            "세부단지명": row.find_element(By.XPATH, "./td[7]").text.strip(),
            "면적": '/'.join(area + "㎡" for area in row.find_element(By.XPATH, "./td[8]").text.strip().split('\n')),
            "가격": row.find_element(By.XPATH, "./td[9]").text.strip(),
        })
        
        # 2단계: 매물 상세 페이지로 이동
        # property_id 링크 클릭
        property_link = driver.find_element(By.XPATH, f"//a[@href=\"javascript:goDetail('{property_id}', 'RB', 'A');\"]")
        property_link.click()
        
        # 3단계: 매물 상세 페이지에서 정보 추출
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        # 상세 필드 정보 추출
        property_fields = {
            "단지명": "건물명",
            "건물종류": "건물종류",
            "건축물용도": "건축물용도",
            "권리금": "권리금",
            "월 관리비": "월 관리비",
            "해당층/총층": "해당층/총층", 
            "방향": "방향",
            "현관구조": "현관구조",
            "방수": "방수",
            "총세대수": "총세대수",
            "욕실수": "욕실수",
            "입주가능일": "입주가능일",
            "총 주차대수": "총 주차대수",
            "건축물용도": "건축물용도",
            "매물특징": "매물특징",
            "상세설명": "상세설명"
        }

        for key, field in property_fields.items():
            try:
                # 모든 th 태그를 찾아서 해당 필드가 포함된 것을 찾기
                for th in soup.find_all('th'):
                    if field in th.text:
                        td = th.find_next('td')
                        field_value = None
                        
                        # textarea 태그 확인
                        if td.find('textarea'):
                            field_value = td.find('textarea').text.strip()
                        
                        # input 태그 확인
                        elif td.find('input', {'class': 'input'}):
                            input_tag = td.find('input', {'class': 'input'})
                            if input_tag.get('value'):
                                field_value = input_tag.get('value').strip()
                        
                        # select 태그 확인
                        elif td.find('select'):
                            selected_option = td.find('select').find('option', selected=True)
                            field_value = selected_option.text.strip() if selected_option else None
                        
                        # 모두 해당 없는 경우 일반 텍스트
                        else:
                            field_value = td.get_text(strip=True)
                            
                        property_data[key] = field_value
                        print(f"[크롤링 데이터] {key}: {field_value}")
                        break
                        
            except Exception as e:
                print(f"[크롤링 실패] {field} 정보 추출 실패: {str(e)}")
                property_data[key] = None

        # 전체 데이터 출력
        print("\n=== 전체 크롤링 데이터 ===")
        for key, value in property_data.items():
            print(f"{key}: {value}")
        print("========================\n")
        
        # 모든 데이터 수집 후
        if '해당층/총층' in property_data:
            floors = property_data['해당층/총층'].replace('\n', '').replace(' ', '').replace('\xa0', '').split('/')
            floors = [f.strip() for f in floors if f.strip()]
            if len(floors) == 2:
                property_data['해당층/총층'] = f"{floors[0]}/{floors[1]}"

        # 4단계: DB 저장
        try:
            complex_name = property_data['단지명']
            apt_collection = db['apt']
            
            # property_data에서 단지명 제거 (복사본 생성)
            property_data_to_save = property_data.copy()
            property_data_to_save.pop('단지명')
            
            existing_complex = apt_collection.find_one({
                "단지명": complex_name,
                "매물목록.매물번호": property_id
            })
            
            if existing_complex:
                result = apt_collection.update_one(
                    {
                        "단지명": complex_name,
                        "매물목록.매물번호": property_id
                    },
                    {"$set": {"매물목록.$": property_data_to_save}}
                )
                print(f"기존 매물 정보 업데이트: {complex_name} - {property_id}")
            else:
                result = apt_collection.update_one(
                    {"단지명": complex_name},
                    {
                        "$push": {"매물목록": property_data_to_save},
                        "$setOnInsert": {"이미지목록": []}
                    },
                    upsert=True
                )
                print(f"새로운 매물 추가: {complex_name} - {property_id}")
            
        except Exception as e:
            print(f"매물 정보 저장 중 오류 발생: {str(e)}")
    except Exception as e:
        print(f"매물 크롤링 중 오류 발생: {str(e)}")

        driver.back()

def check_property_type(driver, property_id):
    """매물 종류 확인"""
    valid_types = ['아파트', '재건축', '주상복합', '오피스텔', '상가점포', '빌라/다세대/연립', '사무실', '단독/다가구']
    
    try:
        # property_id로 해당 매물 행 찾기
        row = driver.find_element(By.XPATH, f"//tr[contains(.//a, '{property_id}')]")
        # 네 번째 td에서 매물 종류 가져오기
        property_type = row.find_element(By.XPATH, "./td[4]").text.strip()
        
        if property_type in valid_types:
            return property_type
        else:
            print("유효한 매물 종류를 찾을 수 없습니다")
            return None
            
    except Exception as e:
        print(f"매물 종류 확인 실패: {str(e)}")
        return None
    
def process_property_info(driver, property_id):
    """매물 종류에 따라 적절한 함수 실행"""
    try:
        property_type = check_property_type(driver, property_id)
        time.sleep(2)

        if property_type in ["아파트", "재건축", "주상복합"]:
            print("아파트 매물 정보 추출 시작")
            return extract_and_save_apt(driver, property_id)
        elif property_type == "상가점포":
            print("상가 매물 정보 추출 시작")
            return extract_and_save_market(driver, property_id)
        elif property_type in ["빌라/다세대/연립", "단독/다가구"]:
            print("빌라 매물 정보 추출 시작")
            return extract_and_save_villa(driver, property_id)
        elif property_type == "오피스텔":
            print("오피스텔 매물 정보 추출 시작")
            return extract_and_save_officetel(driver, property_id)
        elif property_type == "사무실":
            print("사무실 매물 정보 추출 시작")
            return extract_and_save_office(driver, property_id)
        else:
            print(f"처리할 수 없는 매물 종류입니다: {property_type}")
            return None
            
    except Exception as e:
        print(f"매물 정보 처리 중 오류 발생: {str(e)}")
        return None