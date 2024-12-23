from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import pyperclip
import keyboard
import pyautogui
import time

def test_popup_handling():
    driver = webdriver.Chrome()
    actions = ActionChains(driver)
    
    try:
        # 네라우저 최대화
        driver.maximize_window()
        
        # 네이버 블로그 글쓰기 페이지로 이동
        driver.get('https://blog.naver.com/juka103?Redirect=Write&')
        
        # 로그인
        id_input = driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/form/ul/li/div/div[1]/div/div[1]/input')
        id_input.click()
        pyperclip.copy('juka103')  # 실제 아이디로 변경
        actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        time.sleep(1)
        
        pwd_input = driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div/div[1]/form/ul/li/div/div[1]/div/div[2]/input')
        pwd_input.click()
        pyperclip.copy('samik9407!')  # 실제 비밀번호로 변경
        actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        time.sleep(1)
        
        button = driver.find_element(By.XPATH, '//*[@id="log.login"]')
        button.click()
        time.sleep(3)
        
        # 화면 중앙 왼쪽 끝 클릭
        screen_width, screen_height = pyautogui.size()
        pyautogui.click(10, screen_height // 2)  # x좌표를 10으로 설정하여 왼쪽 끝으로
        time.sleep(1)
        
        # tab과 enter 키 입력
        keyboard.press_and_release('tab')
        keyboard.press_and_release('enter')
        
        time.sleep(5)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_popup_handling()