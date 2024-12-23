import os
import random
from typing import List
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import keyboard 

def get_map_images(complex_name: str) -> List[str]:
    """
    단지명 폴더에서 지도(MAPS) 이미지를 찾습니다.
    
    Args:
        complex_name (str): 단지명
    
    Returns:
        List[str]: 지도 이미지들의 전체 경로 리스트
    """
    base_path = r"C:\Users\pqstv\Desktop\real_estate_automization\images"
    complex_path = os.path.join(base_path, complex_name)
    
    if not os.path.exists(complex_path):
        print(f"단지명 폴더를 찾을 수 없습니다: {complex_path}")
        return []  # 빈 리스트 반환
    
    map_files = [f for f in os.listdir(complex_path) 
                if f.upper().startswith('MAPS')
                and f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    
    return [os.path.join(complex_path, img) for img in map_files]

def get_ground_plan_images(complex_name: str) -> List[str]:
    """
    단지명 폴더에서 배치도(GRDPLAN) 이미지를 찾습니다.
    
    Args:
        complex_name (str): 단지명
    
    Returns:
        List[str]: 배치도 이미지들의 전체 경로 리스트
    """
    base_path = r"C:\Users\pqstv\Desktop\real_estate_automization\images"
    complex_path = os.path.join(base_path, complex_name)
    
    if not os.path.exists(complex_path):
        print(f"단지명 폴더를 찾을 수 없습니다: {complex_path}")
        return []  # 빈 리스트 반환
    
    plan_files = [f for f in os.listdir(complex_path) 
                 if f.upper().startswith('GRDPLAN')
                 and f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    
    return [os.path.join(complex_path, img) for img in plan_files]

def select_random_images(complex_name: str, num_images: int = 3) -> List[str]:
    """
    지정된 단지명 폴더에서 랜덤하게 이미지를 선택합니다 (지도와 배치도 제외).
    
    Args:
        complex_name (str): 단지명
        num_images (int): 선택할 이미지 수 (기본값: 3)
    
    Returns:
        List[str]: 선택된 이미지들의 전체 경로 리스트
    """
    base_path = r"C:\Users\pqstv\Desktop\real_estate_automization\images"
    complex_path = os.path.join(base_path, complex_name)
    
    if not os.path.exists(complex_path):
        print(f"단지명 폴더를 찾을 수 없습니다: {complex_path}")
        return []  # 빈 리스트 반환
    
    # 지도와 배치도를 제외한 이미지 파일 가져오기
    image_files = [f for f in os.listdir(complex_path) 
                  if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
                  and not (f.upper().startswith('MAPS') or f.upper().startswith('GRDPLAN') or f.upper().startswith('BILDLINE'))]
    
    if not image_files:
        print(f"경고: 폴더에 이미지 파일이 없습니다: {complex_path}")
        print("이미지 없이 계속 진행합니다.")
        return []  # 빈 리스트 반환
    
    selected_images = random.sample(
        image_files, 
        min(num_images, len(image_files))
    )
    
    return [os.path.join(complex_path, img) for img in selected_images]

def upload_images_to_blog(driver, image_paths: List[str]) -> bool:
    """
    네이버 블로그에 이미지를 업로드합니다.
    
    Args:
        driver: Selenium WebDriver 인스턴스
        image_paths: 업로드할 이미지 경로 리스트
    
    Returns:
        bool: 업로드 성공 여부
    """
    
    actions = ActionChains(driver)
    
    try:
        for file_path in image_paths:
            photo_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-name='image']"))
            )
            driver.execute_script("arguments[0].click();", photo_button)
            time.sleep(2)
            
            print(f"{file_path} 업로드 시도 중...")
            try:
                file_input = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                )
                file_input.send_keys(file_path)
                time.sleep(3)
                print(f"업로드 완료: {file_path}")
                
            except Exception as e:
                print(f"업로드 실패: {file_path} - {e}")
                return False

            time.sleep(1)

        print("모든 사진 업로드가 완료되었습니다.")
        keyboard.press_and_release('esc')
        time.sleep(2)
        return True
        
    except Exception as e:
        print(f"사진 추가 과정에서 오류 발생: {str(e)}")
        return False

def get_specific_image(file_path: str) -> str:
    """
    지정된 경로의 단일 이미지를 가져옵니다.
    
    Args:
        file_path (str): 이미지 파일 경로
    
    Returns:
        str: 이미지 파일의 전체 경로
    
    Raises:
        FileNotFoundError: 파일이 존재하지 않는 경우
        ValueError: 지원하지 않는 파일 형식인 경우
    """
    if not os.path.exists(file_path):
        print(f"지정된 파일을 찾을 수 없습니다: {file_path}")
        return []  # 빈 리스트 반환
    
    if not os.path.isfile(file_path):
        print(f"지정된 경로가 파일이 아닙니다: {file_path}")
        return []  # 빈 리스트 반환
        
    if not file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        print(f"지원하지 않는 파일 형식입니다: {file_path}")
        return []  # 빈 리스트 반환
    
    return file_path
