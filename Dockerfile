# 베이스 이미지
FROM python:3.12.3

# /lecture 폴더 만들기
WORKDIR /lecture

# PYTHONPATH 환경 변수 설정
ENV PYTHONPATH=/lecture/app

# 필요한 패키지 설치를 위해 apt 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y cmake

# ./requirements.txt 를 /lecture/requirements.txt 로 복사
COPY ./requirements.txt /lecture/requirements.txt

# .env 파일 복사
COPY .env /lecture/.env

# pip 업그레이드
RUN pip install --upgrade pip

# requirements.txt 를 보고 모듈 전체 설치(-r)
RUN pip install --no-cache-dir -r /lecture/requirements.txt

# app 에 있는 파일들을 /lecture/app 에 복사
COPY ./app /lecture/app

# 실행 명령어
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
