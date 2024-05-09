# 나의 python 버전
FROM python:3.12.3

# /dorang 폴더 만들기
WORKDIR /lecture

# ./requirements.txt 를 /dorang/requirements.txt 로 복사
COPY ./requirements.txt /lecture/requirements.txt

# requirements.txt 를 보고 모듈 전체 설치(-r)
RUN pip install --no-cache-dir -r /lecture/requirements.txt

# 이제 app 에 있는 파일들을 /code/app 에 복사.
COPY app/main.py /lecture/app/main.py

# 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
