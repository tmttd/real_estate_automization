from services.information_crawling import PropertyCrawler
from services.blog_posting import NaverBlogPoster
import tkinter as tk
from tkinter import simpledialog
import random
import time
from services.automatic_writer import automatic_writer
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

def get_property_id():
    """GUI 창을 통해 사용자로부터 매물번호를 입력받습니다."""
    root = tk.Tk()
    root.withdraw()
    property_id = simpledialog.askstring("매물번호 입력", "매물번호를 입력하세요:")
    root.destroy()
    return property_id

def get_random_user_agent():
    """랜덤 User-Agent 반환"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15'
    ]
    return random.choice(user_agents)

def setup_chrome_options():
    """Selenium 설정 최적화"""
    options = Options()
    options.add_argument(f'user-agent={get_random_user_agent()}')
    
    # 자동화 감지 방지
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 기본 권한 관련 설정
    prefs = {
        "profile.default_content_setting_values.notifications": 1,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    options.add_experimental_option("prefs", prefs)
    
    # 추가 설정
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return options

def add_random_delay():
    """자연스러운 지연 시간 추가"""
    time.sleep(random.uniform(2, 5))

def main():
    # 환경변수에서 설정값 로드
    chrome_driver_path = os.getenv('CHROME_DRIVER_PATH')
    naver_id = os.getenv('NAVER_ID')
    naver_pwd = os.getenv('NAVER_PWD')
    property_user_id = os.getenv('PROPERTY_USER_ID')
    property_password = os.getenv('PROPERTY_PASSWORD')
    save_path = os.getenv('SAVE_PATH')
    
    # 환경변수 확인
    required_env_vars = {
        'CHROME_DRIVER_PATH': chrome_driver_path,
        'NAVER_ID': naver_id,
        'NAVER_PWD': naver_pwd,
        'PROPERTY_USER_ID': property_user_id,
        'PROPERTY_PASSWORD': property_password,
        'SAVE_PATH': save_path
    }
    
    # 필수 환경변수 검증
    missing_vars = [var for var, value in required_env_vars.items() if not value]
    if missing_vars:
        raise EnvironmentError(f"다음 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
    
    # 매물번호 입력받기
    property_id = get_property_id()
    if not property_id:
        print("매물번호가 입력되지 않았습니다.")
        return
    
    # Chrome 옵션 설정 및 드라이버 생성
    chrome_options = setup_chrome_options()
    service = webdriver.ChromeService(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # 1. 매물 정보 크롤링
        crawler = PropertyCrawler(driver=driver)
        add_random_delay()
        
        # 로그인
        crawler.login(property_user_id, property_password)
        add_random_delay()
        
        # 매물 페이지로 이동
        crawler.navigate_to_property_list()
        add_random_delay()
        
        # 매물 정보 크롤링
        if crawler.crawl_property_info(property_id, save_path):
            crawler.print_complex_info()
            add_random_delay()
        else:
            raise Exception("매물 정보 크롤링에 실패했습니다.")
        
        # automatic writer로 컨텐츠 생성
        title, information, description = automatic_writer(property_id)
        
        # 2. 블로그 포스팅
        poster = NaverBlogPoster(driver)
        
        # 매물 정보 조회
        complex_name, property_url = poster.get_property_info(property_id)
        if not complex_name or not property_url:
            raise Exception("매물 정보를 찾을 수 없습니다.")
        
        # 네이버 블로그 로그인
        poster.login(naver_id, naver_pwd)
        add_random_delay()
        
        # 포스트 작성
        poster.write_post(title, information, description, complex_name, property_url)
        add_random_delay()
        
        # 발행
        if poster.publish_post():
            print("포스트가 성공적으로 발행되었습니다.")
        else:
            print("포스트 발행에 실패했습니다.")
            
    except Exception as e:
        print(f"작업 중 오류 발생: {str(e)}")
        
    finally:
        # 작업 완료 후 사용자 입력 대기
        print("작업이 완료되었습니다. 브라우저를 3초 뒤 종료합니다.")
        time.sleep(3)
        driver.quit()

if __name__ == "__main__":
    main()