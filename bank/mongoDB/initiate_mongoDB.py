from pymongo import MongoClient

# MongoDB 연결
client = MongoClient('mongodb://localhost:27017/')

# 기존 데이터베이스 삭제
client.drop_database('property_db')

# 새 데이터베이스 생성
db = client['property_db']

# 새 컬렉션들 생성
collections = [
    'apt',          # 아파트
    'commercial',   # 상가
    'villa',             # 빌라
    'officetel',         # 오피스텔
    'office'             # 사무실
]

for collection_name in collections:
    db.create_collection(collection_name)

print("MongoDB 리셋 완료")
print("생성된 컬렉션:", db.list_collection_names())