import uvicorn
from dataclasses import asdict
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.conn import db
from dependencies import get_query_token, get_token_header
from internal import admin
from routers import items, users, auth, members
from app.common.config import conf

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

app.include_router(auth.router)
app.include_router(members.router)
app.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_token_header)],
    responses={418: {"description": "I'm a teapot"}},
)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)