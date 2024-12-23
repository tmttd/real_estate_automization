from openai import OpenAI
from pymongo import MongoClient
import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import simpledialog
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# OpenAI API 키를 환경변수에서 가져오기
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# MongoDB 연결
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['property_db']
collections = {
    'apt': db['apt'],
    'commercial': db['commercial'],
    'villa': db['villa'],
    'officetel': db['officetel'],
    'office': db['office']
}

def get_property_id():
    root = tk.Tk()
    root.withdraw()  # 기본 창 숨기기
    
    # 팝업 창으로 입력 받기
    property_id = simpledialog.askstring("입력", "네이버 매물번호를 입력하세요:")
    
    return property_id

def get_property_data(property_id):
    """MongoDB의 모든 컬렉션에서 매물 정보와 컬렉션 타입 찾기"""
    for collection_name, collection in collections.items():
        # 매물목록 배열 내부의 매물번호로 검색
        property_data = collection.find_one({"매물목록.매물번호": property_id})
        if property_data:
            # 매물목록에서 해당 매물 정보 찾기
            for item in property_data['매물목록']:
                if item['매물번호'] == property_id:
                    # 매물 정보에 컬렉션 타입과 이미지 목록 추가
                    item['매물종류'] = collection_name
                    item['이미지목록'] = property_data.get('이미지목록', [])
                    item['단지명'] = property_data['단지명']  # 상위 문서의 단지명 추가
                    return item
    return None

def generate_blog_title(property_data):
    """OpenAI API를 사용하여 블로그 글 제목 생성"""
    try:
        # 프롬프트 작성
        prompt = f"""
        모든 내용은 한국어로 번역해서 작성하세요.
        다음 부동산 매물 정보를 반영하여 블로그 글 제목을 작성해주세요.
        진하게 표시하기 위한 * 기호는 절대 사용하지 말아주세요.
        
        매물 정보:
        - 단지명: {property_data.get('단지명', '정보 없음')}
        - 세부단지명: {property_data.get('세부단지명', '정보 없음')}
        - 매물종류: {property_data.get('매물종류', '정보 없음')}
        - 거래종류: {property_data.get('거래종류', '정보 없음')}
        - 면적: {property_data.get('공급/전용면적', '정보 없음') or property_data.get('계약/전용면적', '정보 없음')}
        - 해당층/총층: {property_data.get('해당층/총층', '정보 없음')}
        
        반드시 예외없이 무조건 다음 형식에 맞게 작성해 주세요. 없는 것은 생략해주세요.
        \[단지명\] 세부단지명 매물종류 공급면적 계약면적 거래종류(해당층/총층)
        
        다음 영어는 한국어로 번역하세요.
          예시) 'officetel' -> '오피스텔', 'office'-> '사무실', 'commercial' -> '상가', 'villa' -> '빌라', 'apt' -> '아파트'
        """

        # API 호출
        response = client.chat.completions.create(
            model="gpt-4o",  # 또는 "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "당신은 전문적인 매물 정보 게시글 작성자입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        # 생성된 컨텐츠 반환
        return response.choices[0].message.content

    except Exception as e:
        print(f"컨텐츠 생성 중 오류 발생: {str(e)}")
        return None

def generate_estate_information(property_data):
    """OpenAI API를 사용하여 블로그 컨텐츠 생성"""
    try:
        # 프롬프트 작성
        prompt = f"""        
        <다음 구조로 작성해주세요.>
        
        1. 다음 문구를 맨 앞에 적으세요. '정보 없음'만 삭제해 주세요.
          *** {property_data.get('세부단지명', '정보 없음')} {property_data.get('매물종류', '정보 없음')} {property_data.get('공급/전용면적', '정보 없음') or property_data.get('계약/전용면적', '정보 없음')} {property_data.get('거래종류', '정보 없음')}({property_data.get('해당층/총층', '정보 없음')}) 정보입니다. ***
        
        2. 다음 내용을 '정보 없음'만 삭제하고 그대로 개조식으로 작성해 주세요.
        
        3. 기호를 사용하지 말아 주세요.
        
        매물 정보:
         가격: {property_data.get('가격', '정보 없음')}
         세부단지명: {property_data.get('세부단지명', '정보 없음')}
         매물특징: {property_data.get('매물특징', '정보 없음')}
         매물종류: {property_data.get('매물종류', '정보 없음')}
         소재지: {property_data.get('소재지', '정보 없음')}
         거래종류: {property_data.get('거래종류', '정보 없음')}
         면적: {property_data.get('공급/전용면적', '정보 없음') or property_data.get('계약/전용면적', '정보 없음')}
         해당층/총층: {property_data.get('해당층/총층', '정보 없음')}
         입주가능일: {property_data.get('입주가능일', '정보 없음')}
         방향: {property_data.get('방향', '정보 없음')}
         관리비: {property_data.get('관리비', '정보 없음')}
         월관리비: {property_data.get('월관리비', '정보 없음')}
         총주차대수: {property_data.get('총주차대수', '정보 없음')}
         주차가능여부: {property_data.get('주차가능여부', '정보 없음')}
         난방: {property_data.get('난방(방식/연료)', '정보 없음')}
         현관구조: {property_data.get('현관구조', '정보 없음')}
         방수/욕실수: {property_data.get('방수/욕실수', '정보 없음')}
         현재업종: {property_data.get('현재업종', '정보 없음')}
         추천업종: {property_data.get('추천업종', '정보 없음')}
         건축물용도: {property_data.get('건축물용도', '정보 없음')}
         해당면적세대수: {property_data.get('해당면적세대수', '정보 없음')}
        
        <다음을 반드시 지켜주세요.>
         1. '정보 없음'은 반드시 무시하세요.
         2. 가격은 대한민국에서 사용하는 화폐 단위에 알맞게 변환해서 표시해주세요.(10000 만원 -> 1억)
         3. 다음 영어는 한국어로 번역하세요.
          예시) 'officetel' -> '오피스텔', 'office'-> '사무실', 'commercial' -> '상가', 'villa' -> '빌라', 'apt' -> '아파트'
         4. 이 외에는 문구를 절대 작성하지 마세요.
        """

        # API 호출
        response = client.chat.completions.create(
            model="gpt-4o",  # 또는 "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "당신은 전문적인 매물 정보 게시글 작성자입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        # 생성된 컨텐츠 반환
        return response.choices[0].message.content

    except Exception as e:
        print(f"컨텐츠 생성 중 오류 발생: {str(e)}")
        return None

def generate_estate_description(property_data):
    """OpenAI API를 사용하여 블로그 컨텐츠 생성"""
    try:
        # 프롬프트 작성
        prompt = f"""
        다음 부동산 매물 정보를 반드시 모두 포함하여 매물 설명을 작성해주세요.
        글은 자연스럽고 신뢰감 있는 톤으로 작성해주세요.
        가격은 대한민국에서 사용하는 화폐 단위에 알맞게 변환해서 표시해주세요.(10000 만원 -> 1억)
        
        매물 정보:
        - 매물종류: {property_data.get('매물종류', '정보 없음')}
        - 소재지: {property_data.get('소재지', '정보 없음')}
        - 거래종류: {property_data.get('거래종류', '정보 없음')}
        - 가격: {property_data.get('가격', '정보 없음')}
        - 면적: {property_data.get('공급/전용면적', '정보 없음') or property_data.get('계약/전용면적', '정보 없음')}
        - 층수: {property_data.get('해당층/총층', '정보 없음')}
        - 입주가능일: {property_data.get('입주가능일', '정보 없음')}
        - 특징: {property_data.get('매물특징', '정보 없음')}
        - 방향: {property_data.get('방향', '정보 없음')}
        - 관리비: {property_data.get('관리비', '')}
        - 월관리비: {property_data.get('월관리비', '정보 없음')}
        - 주차: {property_data.get('총주차대수', '')}
        - 주차가능여부: property_data.get('주차가능여부', '정보 없음')
        - 난방: {property_data.get('난방(방식/연료)', '정보 없음')}
        - 현관구조: {property_data.get('현관구조', '정보 없음')}
        - 방수/욕실수: {property_data.get('방수/욕실수', '정보 없음')}
        - 현재업종: {property_data.get('현재업종', '정보 없음')}
        - 추천업종: {property_data.get('추천업종', '정보 없음')}
        - 건축물용도: {property_data.get('건축물용도', '정보 없음')}
        - 해당면적세대수: {property_data.get('해당면적세대수', '정보 없음')}
        - 매물설명: {property_data.get('매물설명', '정보 없음')}
        
        <다음 구조로 작성해주세요>
        1. 매물 설명을 반드시 참조하세요.
        2. 과도하지 않은 판촉 문구를 작성해주세요. (매물의 장점과 특징, 투자 가치나 실거주 가치 등)
        3. (반드시 수정하지 말고 이대로 작성) 010-8751-5430로 연락 주시면 자세한 상담 가능합니다.
        
        <다음을 반드시 지켜주세요>
        1. 인사말은 생략하세요.
        2. '정보 없음'은 반드시 무시하세요.
        3. 사실이 아닌 정보를 절대 작성하지 마세요.
        """

        # API 호출
        response = client.chat.completions.create(
            model="gpt-4o",  # 또는 "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "당신은 전문적인 매물 정보 게시글 작성자입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        # 생성된 컨텐츠 반환
        return response.choices[0].message.content

    except Exception as e:
        print(f"컨텐츠 생성 중 오류 발생: {str(e)}")
        return None

def save_blog_content(property_id, content):
    """생성된 블로그 컨텐츠 저장"""
    try:
        # 저장할 디렉토리 생성
        save_dir = "generated_contents"
        os.makedirs(save_dir, exist_ok=True)
        
        # 파일명 생성 (매물번호_날짜.txt)
        filename = f"{save_dir}/{property_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # 컨텐츠 저장
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"블로그 컨텐츠가 {filename}에 저장되었습니다.")
        return filename
        
    except Exception as e:
        print(f"컨텐츠 저장 중 오류 발생: {str(e)}")
        return None

def automatic_writer(property_id=None):
    """메인 실행 함수"""
    # property_id가 없을 경우에만 사용자 입력 받기
    if property_id is None:
        property_id = get_property_id()
        if not property_id:
            return None, None, None
    
    # 매물 정보 가져오기
    property_data = get_property_data(property_id)
    if not property_data:
        print(f"매물 정보를 찾을 수 없습니다: {property_id}")
        return None, None, None  # 세 개의 값을 반환
    
    # 블로그 제목 생성
    title = generate_blog_title(property_data)
    if not title:
        print("블로그 제목 생성에 실패했습니다.")
        return None, None, None
    
    # 블로그 매물 정보 생성
    information = generate_estate_information(property_data)
    if not information:
        print("블로그 매물 정보 생성에 실패했습니다.")
        return None, None, None
    
    # 블로그 매물 설명 생성
    description = generate_estate_description(property_data)
    if not description:
        print("블로그 매물 설명 생성에 실패했습니다.")
        return None, None, None

    return title, information, description
