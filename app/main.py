import uvicorn
from dataclasses import asdict
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.database.conn import db
from dependencies import get_query_token, get_token_header
from internal import admin
from routers import course, auth, members, classBooking
from app.common.config import conf
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.common.consts import JWT_SECRET, JWT_ALGORITHM

# 인증 설정
security = HTTPBearer()

# JWT 토큰 검증 함수
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=JWT_ALGORITHM)
        return payload
    except JWTError:
        raise HTTPException(
            status_code=403, detail="Invalid authentication credentials"
        )


c = conf()
#app = FastAPI(dependencies=[Depends(get_query_token)])
app = FastAPI()
conf_dict = asdict(c)
db.init_app(app, **conf_dict)

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 또는 특정 도메인을 지정할 수 있습니다.
    allow_credentials=True,
    allow_methods=["*"],  # 모든 메서드를 허용합니다. 특정 메서드만 허용할 수도 있습니다.
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(members.router, prefix="/members", tags=["members"], dependencies=[Depends(verify_token)])
app.include_router(course.router, prefix="/course", tags=["course"], dependencies=[Depends(verify_token)])
app.include_router(classBooking.router, prefix="/class-booking", tags=["class-booking"], dependencies=[Depends(verify_token)])

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)