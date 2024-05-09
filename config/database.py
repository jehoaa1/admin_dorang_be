import os
import pymysql
from dotenv import load_dotenv

# .env 파일을 읽어옵니다.
load_dotenv()

# 데이터베이스 연결 정보를 가져옵니다.
db_host = os.getenv("DB_HOST")
db_port = int(os.getenv("DB_PORT"))
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

# 데이터베이스에 연결합니다.
def db_connect():
    aconn = pymysql.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )
    return aconn
