import json
import math

import requests
import xmltodict
from kafka import KafkaProducer

# 카프카 서버 ip
KAFKA_SERVER = '10.100.54.43:9092'
# 카프카 토픽 name
KAFKA_TOPIC = 'testApi4'

# API 관련 상수
API_BASE_URL = "https://open.kci.go.kr/po/openapi/openApiSearch.kci"
API_CODE = "articleSearch"
API_KEY = "31446398"
API_TITLE = "컴퓨터"
API_DISPLAY_COUNT = 100

# 논문 데이터 API 주소 생성 함수
def generate_api_url(page):
    return f"{API_BASE_URL}?apiCode={API_CODE}&key={API_KEY}&title={API_TITLE}&displayCount={API_DISPLAY_COUNT}&page={page}"

# process_api_response로 처리한 데이터를 카프카에 전송하는 함수
def send_data_to_kafka(data):
    try:
        print(data)
        producer.send(KAFKA_TOPIC, value=data)
    except Exception as e:
        print("Error occurred:", str(e))

# response를 파싱하는 함수
def process_api_response(api_response):
    content = api_response.content
    dict_type = xmltodict.parse(content)
    outputData = dict_type['MetaData']['outputData']
    record_list = outputData.get('record', [])

    for record in record_list:
        article_info = record['articleInfo']
        author_group = article_info['author-group']
        authors = author_group.get('author', [])

        for author in authors:
            author_name = author.strip()
            print(author_name)
            send_data_to_kafka({'author': author_name})


# Kafka producer 객체
producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER, value_serializer=lambda x: json.dumps(x).encode('utf-8'))

try:
    # 최초의 API 요청을 보내서 전체 아이템 개수를 얻음
    response = requests.get(generate_api_url(1))
    if response.status_code == 200:
        process_api_response(response)

        # Pagination 처리를 위한 추가 작업
        content = response.content
        dict_type = xmltodict.parse(content)
        metadata = dict_type['MetaData']
        total_items = int(metadata['outputData']['result']['total'])
        max_pages = math.ceil(total_items / API_DISPLAY_COUNT)
        print(max_pages)

        # 각 페이지에 대해 API 요청 반복
        for page in range(2, max_pages + 1):
            response = requests.get(generate_api_url(page))
            if response.status_code == 200:
                process_api_response(response)
            else:
                print(f"API request failed for page {page}.")
    else:
        print("API request failed.")
except requests.exceptions.RequestException as e:
    print("Error occurred during API request:", str(e))
