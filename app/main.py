import uvicorn
from dataclasses import asdict
from fastapi import Depends, FastAPI

from app.database.conn import db
from dependencies import get_query_token, get_token_header
from internal import admin
from routers import items, users, auth
from app.common.config import conf

c = conf()
app = FastAPI(dependencies=[Depends(get_query_token)])
conf_dict = asdict(c)
db.init_app(app, **conf_dict)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(items.router)
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