# 🎯 아트히어로 백엔드 - FastAPI 기반 학원 관리 시스템.

## 📌 개요

- **백엔드 프레임워크**: FastAPI
- **데이터베이스**: MySQL (AWS RDS)
- **인증 방식**: JWT
- **배포 환경**: Docker, AWS EC2
- **CI/CD**: GitHub Actions

## 🔧 주요 기능

1. **회원가입 / 로그인**
   - JWT 기반 인증 및 토큰 발급
2. **학생 관리 API**
   - 학생 등록, 조회, 수정, 삭제
3. **강의 관리 API**
   - 강의 정보 등록 및 일정 관리
4. **결제 관리 API**
   - 수강료 등록 및 결제 내역 조회

## 🧪 테스트

- Swagger UI를 통한 API 문서 제공 (`/docs`)

## ⚙️ 실행 방법

1. **가상환경 설정 및 패키지 설치**

```bash
python -m venv venv
source venv/bin/activate  # 윈도우는 venv\Scripts\activate
pip install -r requirements.txt
```

2. **환경변수 파일 설정 (.env)**

```env
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
AWS_S3_ACCESS_KEY=
AWS_S3_PRIVATE_KEY=
AWS_S3_BUCKET_NAME=
```

3. **서버 실행**

```bash
uvicorn app.main:app --reload
```

## 🐳 Docker 실행

```bash
docker build -t arthero-backend .
docker run -d -p 8000:8000 --env-file .env arthero-backend
```

## 🧾 API 문서

- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
