from pymongo import MongoClient

# MongoDB 연결 설정
client = MongoClient('mongodb://localhost:27017/')
db = client['property_db']

def save_image_info_to_mongodb(property_id, category, img_url, file_path, category_count):
    """이미지 정보를 단지 수준에서 MongoDB에 저장"""
    try:
        # 여러 컬렉션에서 검색
        collections = {
            'apt': db['apt'],
            'officetel': db['officetel']
        }
        
        property_data = None
        collection = None
        
        # 각 컬렉션에서 매물 검색
        for coll_name, coll in collections.items():
            data = coll.find_one({"매물목록.매물번호": property_id})
            if data:
                property_data = data
                collection = coll
                break
        
        if not property_data:
            print("해당 매물이 속한 단지 정보를 찾을 수 없습니다.")
            return
            
        # 이미지 정보 추가
        result = collection.update_one(
            {
                "단지명": property_data['단지명'],
                "이미지목록": {
                    "$not": {
                        "$elemMatch": {
                            "카테고리": category,
                            "카테고리순번": category_count
                        }
                    }
                }
            },
            {"$push": {"이미지목록": {
                "카테고리": category,
                "이미지URL": img_url,
                "저장경로": file_path,
                "카테고리순번": category_count
            }}}
        )
        
        print(f"이미지 저장 완료: {property_data['단지명']} - {category}_{category_count}")
            
    except Exception as e:
        print(f"이미지 정보 저장 중 오류 발생: {str(e)}")