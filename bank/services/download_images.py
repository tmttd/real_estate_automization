from pymongo import MongoClient
from selenium.webdriver.common.by import By
import time
import os
import requests
from .save_image_info_to_mongodb import save_image_info_to_mongodb

# MongoDB 연결 설정
client = MongoClient('mongodb://localhost:27017/')
db = client['property_db']

def download_images(driver, property_id, path):
    
    # 매물번호로 해당 td를 찾고, 그 안에서 ReportGbn이 포함된 링크를 클릭
    report_link = driver.find_element(By.XPATH, f"//td[contains(.//a, '{property_id}')]//a[contains(@href, 'ReportGbn')]")
    report_link.click()
    time.sleep(2)
    
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(2)
    current_url = driver.current_url
    
    # 모든 컬렉션에서 URL 업데이트
    collections = ['apt', 'officetel', 'commercial', 'office', 'villa']
    for collection_name in collections:
        collection = db[collection_name]
        collection.update_one(
            {"매물목록.매물번호": property_id},
            {"$set": {"매물목록.$.URL": current_url}}
        )
    print(f"매물 {property_id}의 URL 업데이트 완료: {current_url}")
    
    # apt나 officetel 컬렉션에 있는 매물인지 확인
    property_data = None
    collection_name = None
    
    for name in ['apt', 'officetel']:
        collection = db[name]
        data = collection.find_one({"매물목록.매물번호": property_id})
        if data:
            property_data = data
            collection_name = name
            break
            
    if not property_data:
        print("apt/officetel 컬렉션에 속한 매물이 아닙니다.")
        return
            
    building_name = property_data['단지명']  # apt나 officetel 모두 '단지명' 사용
        
    # 이미 이미지가 있는지 확인
    if property_data.get('이미지목록', []):
        print(f"건물 '{building_name}'의 이미지가 이미 존재합니다. 다운로드를 건너뜁니다.")
        return
    
    # 문자열 사용해서 단지 고유 번호 추출
    complex_no = current_url.split("/complexes/")[1].split("?")[0]
    print(complex_no)
    
    main_window = driver.window_handles[-1]
    
    # 사진 페이지 이동
    driver.get(f"https://land.naver.com/info/complexGallery.naver?rletNo={complex_no}&newComplex=Y")
    time.sleep(2)

    # 새로 열린 팝업 창으로 전환
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(2)
    
    try:
        # 이미지 요소들이 있는 li 태그들 찾기
        image_items = driver.find_elements(By.CSS_SELECTOR, "ul.lst_view li._js_thumbnail_image_item_view")
        
        if not image_items:
            print(f"매물 {property_id}의 이미지가 없습니다.")
            return
        
        save_path = f"{path}/{building_name}"
        
        # 저장 경로가 없으면 생성
        os.makedirs(save_path, exist_ok=True)
        
        # 카테고리별 카운터 초기화
        category_counters = {}
        
        # 각 이미지 다운로드
        for item in image_items:
            try:
                category = item.get_attribute('_categorycode')
                img = item.find_element(By.TAG_NAME, 'img')
                img_url = img.get_attribute('src')
                img_url = img_url.replace('?type=m70', '')
                
                if category not in category_counters:
                    category_counters[category] = 1
                else:
                    category_counters[category] += 1
                
                response = requests.get(img_url)
                if response.status_code == 200:
                    file_name = f"{category}_{category_counters[category]}.jpg"
                    file_path = os.path.join(save_path, file_name)
                    
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    print(f"이미지 다운로드 완료: {file_name}")
                    
                    # MongoDB에 이미지 정보 저장
                    save_image_info_to_mongodb(
                        property_id=property_id,
                        category=category,
                        img_url=img_url,
                        file_path=file_path,
                        category_count=category_counters[category]
                    )
                else:
                    print(f"이미지 다운로드 실패 ({building_name}_{category}_{category_counters[category]}): HTTP {response.status_code}")
            
            except Exception as e:
                print(f"이미지 처리 중 오류 발생: {str(e)}")
                continue
        
        print(f"매물 {property_id}의 모든 이미지 다운로드 완료")
        print("카테고리별 이미지 수:", category_counters)
    
    except Exception as e:
        print(f"이미지 다운로드 중 오류 발생: {str(e)}")