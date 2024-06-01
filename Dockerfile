# 나의 python 버전
FROM python:3.12.3

# /lecture 폴더 만들기
WORKDIR /lecture

# PYTHONPATH 환경 변수 설정
ENV PYTHONPATH=/lecture/app

# ./requirements.txt 를 /lecture/requirements.txt 로 복사
COPY ./requirements.txt /lecture/requirements.txt
# .env 파일 복사
COPY .env /lecture/.env

# requirements.txt 를 보고 모듈 전체 설치(-r)
RUN pip install --no-cache-dir -r /lecture/requirements.txt

# 이제 app 에 있는 파일들을 /lecture/app 에 복사.
COPY ./app /lecture/app

# 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
