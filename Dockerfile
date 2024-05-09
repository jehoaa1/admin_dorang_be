# 베이스 이미지 설정
FROM python:3.12.3

# 작업 디렉토리 설정
WORKDIR /lecture

# requirements.txt 복사 및 패키지 설치
COPY ./requirements.txt /lecture/requirements.txt
RUN pip install --no-cache-dir -r /lecture/requirements.txt

# 모든 소스 코드 복사
COPY ./app /lecture/app

# 실행 명령어 설정
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
