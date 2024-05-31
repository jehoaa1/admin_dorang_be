from datetime import datetime, timedelta

import bcrypt
import jwt
from jose import JWTError
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
# TODO:
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.common.consts import JWT_SECRET, JWT_ALGORITHM
from app.database.conn import db
from app.database.schema import Users
from app.models import SnsType, Token, UserToken, UserRegister, CustomResponse

router = APIRouter()
security = HTTPBearer()

@router.post("/register/{sns_type}", status_code=201, tags=["auth"], response_model=CustomResponse)
async def register(sns_type: SnsType, reg_info: UserRegister, session: Session = Depends(db.session)):
    """
    `회원가입 API`\n
    :param sns_type:
    :param reg_info:
    :param session:
    :return:
    """
    try:
        if sns_type == SnsType.email:
            is_exist = await is_email_exist(reg_info.email)
            if not reg_info.email or not reg_info.pw:
                raise HTTPException(status_code=400, detail="메일 또는 비밀번호 정보가 없습니다.")
            if is_exist:
                raise HTTPException(status_code=400, detail="가입된 메일 정보")

            hash_pw = bcrypt.hashpw(reg_info.pw.encode("utf-8"), bcrypt.gensalt())
            new_user = Users.create(session, auto_commit=True, pw=hash_pw, email=reg_info.email, sns_type="E", name=reg_info.name)

            # 필드 일치 여부 확인
            try:
                token_data = UserToken.from_orm(new_user).dict(exclude={'pw', 'marketing_agree'})
                logging.info(f"token_data === {token_data}")
            except Exception as ve:
                logging.error(f"Validation error: {ve}")
                raise HTTPException(status_code=400, detail="Validation Error: Incorrect UserToken fields")

            token = dict(Authorization=f"Bearer {create_access_token(data=token_data, expires_delta=10)}")
            return CustomResponse(
                result="success",
                result_msg="회원가입 성공",
                response={"result":"회원가입 성공"}
            )
        else:
            raise HTTPException(status_code=400, detail="NOT_SUPPORTED")
    except HTTPException as e:
        logging.error(f"Error occurred: {str(e)}")
        return CustomResponse(
            result="fail",
            result_msg=str(e.detail),
            response={"status_code": e.status_code}
        )

@router.get("/mail-chk/{email}", status_code=200, tags=["auth"], response_model=CustomResponse)
def get_user(email: str):
    try:
        user = Users.get(email=email)
        if user:
            raise HTTPException(status_code=409, detail="가입 된 메일")
        return CustomResponse(
            result="success",
            result_msg="이용가능",
            response={"result": True}
        )
    except HTTPException as e:
        # 예외 발생 시 로그 기록
        logging.error(f"Error occurred: {e}")
        return CustomResponse(
            result="fail",
            result_msg=str(e.detail),
            response={"status_code": e.status_code}
        )

@router.post("/login/{sns_type}", status_code=200, tags=["auth"], response_model=CustomResponse)
async def login(sns_type: SnsType, user_info: UserRegister):
    try:
        if sns_type == SnsType.email:
            is_exist = await is_email_exist(user_info.email)
            if not user_info.email or not user_info.pw:
                raise HTTPException(status_code=400, detail="Email and PW must be provided")
            if not is_exist:
                raise HTTPException(status_code=400, detail="NO_MATCH_USER")
            user = Users.get(email=user_info.email)
            is_verified = bcrypt.checkpw(user_info.pw.encode("utf-8"), user.pw.encode("utf-8"))
            if not is_verified:
                raise HTTPException(status_code=400, detail="NO_MATCH_USER")
            token_data = UserToken.from_orm(user).dict(exclude={'pw', 'marketing_agree'})

            token = dict(
                Authorization=f"Bearer {create_access_token(data=token_data, expires_delta=10)}")

            return CustomResponse(
                result="success",
                result_msg="로그인 성공",
                response=token
            )
    except HTTPException as e:
        return CustomResponse(
            result="fail",
            result_msg="로그인 실패",
            response={"status_code": "401"})

# verify_token_route 엔드포인트
@router.post("/verify-token", status_code=200, tags=["auth"])
def verify_token_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    decoded_token = decode_access_token(token)
    return {"message": "Token is valid", "payload": decoded_token}

async def is_email_exist(email: str):
    get_email = Users.get(email=email)
    if get_email:
        return True
    return False


def create_access_token(*, data: dict = None, expires_delta: int = None):
    to_encode = data.copy()
    if expires_delta:
        to_encode.update({"exp": datetime.now() + timedelta(hours=expires_delta)})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=JWT_ALGORITHM)
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
