from pymongo import MongoClient
from pprint import pprint

def show_all_mongodb_data():
    """MongoDB의 모든 컬렉션의 모든 데이터를 출력"""
    client = MongoClient('mongodb://localhost:27017/')
    db = client['property_db']
    
    print("\n=== MongoDB 전체 데이터 ===")
    for collection_name in db.list_collection_names():
        print(f"\n[{collection_name} 컬렉션]")
        print("=" * 50)
        
        collection = db[collection_name]
        documents = list(collection.find({}))
        
        if not documents:
            print("데이터 없음")
            continue
            
        for doc in documents:
            pprint(doc)
            print("-" * 50)
    
    client.close()

def show_collection_data(collection_name):
    """특정 컬렉션의 모든 데이터를 출력"""
    client = MongoClient('mongodb://localhost:27017/')
    db = client['property_db']
    
    if collection_name not in db.list_collection_names():
        print(f"Error: '{collection_name}' 컬렉션이 존재하지 않습니다.")
        print("사용 가능한 컬렉션:", db.list_collection_names())
        client.close()
        return
    
    print(f"\n=== {collection_name} 컬렉션 데이터 ===")
    print("=" * 50)
    
    collection = db[collection_name]
    documents = list(collection.find({}))
    
    if not documents:
        print("데이터 없음")
    else:
        for doc in documents:
            pprint(doc)
            print("-" * 50)
    
    client.close()

# 사용 예시:
if __name__ == "__main__":
    # 전체 데이터 조회
    show_all_mongodb_data()
    
    # 특정 컬렉션 데이터 조회
    # show_collection_data('apt')
    # show_collection_data('commercial')
    # show_collection_data('villa')
    # show_collection_data('officetel')
    # show_collection_data('office')    
