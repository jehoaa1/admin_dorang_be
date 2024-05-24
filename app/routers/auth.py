from datetime import datetime, timedelta

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException
import logging
# TODO:
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.common.consts import JWT_SECRET, JWT_ALGORITHM
from app.database.conn import db
from app.database.schema import Users
from app.models import SnsType, Token, UserToken, UserRegister

router = APIRouter(prefix="/auth")


@router.post("/register/{sns_type}", status_code=201, response_model=Token)
async def register(sns_type: SnsType, reg_info: UserRegister, session: Session = Depends(db.session)):
    """
    `회원가입 API`\n
    :param sns_type:
    :param reg_info:
    :param session:
    :return:
    """

    # data = {'user': 'test'}
    #
    # # 추가 클레임을 데이터에 병합
    # additional_claims = {"aud": "some_audience", "foo": "bar"}
    # data.update(additional_claims)
    #
    # # JWT 토큰 생성 (만료 시간 1시간 설정 예시)
    # token = dict(
    #     Authorization=f"Bearer {create_access_token(data=data, expires_delta=1)}"
    # )
    # return token

    try:
        if sns_type == SnsType.email:
            is_exist = await is_email_exist(reg_info.email)
            if not reg_info.email or not reg_info.pw:
                raise HTTPException(status_code=400, detail="Email and PW must be provided")
            if is_exist:
                raise HTTPException(status_code=400, detail="EMAIL_EXISTS")

            hash_pw = bcrypt.hashpw(reg_info.pw.encode("utf-8"), bcrypt.gensalt())
            new_user = Users.create(session, auto_commit=True, pw=hash_pw, email=reg_info.email, sns_type="E")

            logging.info("User created successfully")

            # 필드 일치 여부 확인
            try:
                token_data = UserToken.from_orm(new_user).dict(exclude={'pw', 'marketing_agree'})
                logging.info(f"token_data === {token_data}")
            except Exception as ve:
                logging.error(f"Validation error: {ve}")
                raise HTTPException(status_code=400, detail="Validation Error: Incorrect UserToken fields")

            token = dict(Authorization=f"Bearer {create_access_token(data=token_data, expires_delta=1)}")
            return token
        else:
            raise HTTPException(status_code=400, detail="NOT_SUPPORTED")
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/login/{sns_type}", status_code=200, response_model=Token)
async def login(sns_type: SnsType, user_info: UserRegister):
    if sns_type == SnsType.email:
        is_exist = await is_email_exist(user_info.email)
        if not user_info.email or not user_info.pw:
            return JSONResponse(status_code=400, content=dict(msg="Email and PW must be provided'"))
        if not is_exist:
            return JSONResponse(status_code=400, content=dict(msg="NO_MATCH_USER"))
        print("===============")
        user = Users.get(email=user_info.email)
        print(f"user === {user}")
        is_verified = bcrypt.checkpw(user_info.pw.encode("utf-8"), user.pw.encode("utf-8"))
        if not is_verified:
            return JSONResponse(status_code=400, content=dict(msg="NO_MATCH_USER"))
        token_data = UserToken.from_orm(user).dict(exclude={'pw', 'marketing_agree'})
        print(f"token_data === {token_data}")
        token = dict(
            Authorization=f"Bearer {create_access_token(data=token_data, expires_delta=1)}")
        return token
    return JSONResponse(status_code=400, content=dict(msg="NOT_SUPPORTED"))


async def is_email_exist(email: str):
    get_email = Users.get(email=email)
    if get_email:
        return True
    return False


def create_access_token(*, data: dict = None, expires_delta: int = None):
    to_encode = data.copy()
    if expires_delta:
        to_encode.update({"exp": datetime.utcnow() + timedelta(hours=expires_delta)})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt
