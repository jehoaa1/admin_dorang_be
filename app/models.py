from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Any

from pydantic import Field
from pydantic.main import BaseModel


class UserRegister(BaseModel):
    email: str = None
    pw: str = None
    name: str = None

class MemberRegister(BaseModel):
    name: str = None
    phone: Optional[str] = None
    parent_phone: str = None
    institution_name: Optional[str] = None
    birth_day: datetime

class CourseRegister(BaseModel):
    members_id: int
    start_date: datetime
    end_date: datetime
    session_count: int
    phone: Optional[str] = None
    parent_phone: str = None
    institution_name: Optional[str] = None


class SnsType(str, Enum):
    email: str = "email"
    facebook: str = "facebook"
    google: str = "google"
    kakao: str = "kakao"


class Token(BaseModel):
    Authorization: str = None

class CustomResponse(BaseModel):
    result: str
    result_msg: str
    response: Any

class EmailRecipients(BaseModel):
    name: str
    email: str


class SendEmail(BaseModel):
    email_to: List[EmailRecipients] = None


class KakaoMsgBody(BaseModel):
    msg: str = None


class MessageOk(BaseModel):
    message: str = Field(default="OK")


class UserToken(BaseModel):
    id: int
    email: Optional[str] = None
    name: Optional[str] = None
    sns_type: Optional[str] = None

    class Config:
        from_attributes = True


class UserMe(BaseModel):
    id: int
    email: str = None
    name: str = None
    phone_number: str = None
    profile_img: str = None
    sns_type: str = None

    class Config:
        from_attributes = True


class MembersBase(BaseModel):
    id: int
    name: Optional[str] = None
    phone: Optional[str] = None
    parent_phone: str
    institution_name: Optional[str] = None
    birth_day: date

    class Config:
        from_attributes = True

class CourseBase(BaseModel):
    id: int
    members_id: int
    start_date: datetime
    end_date: datetime
    session_count: int
    payment_amount: int

    class Config:
        from_attributes = True

class AddApiKey(BaseModel):
    user_memo: str = None

    class Config:
        from_attributes = True


class GetApiKeyList(AddApiKey):
    id: int = None
    access_key: str = None
    created_at: datetime = None


class GetApiKeys(GetApiKeyList):
    secret_key: str = None


class CreateAPIWhiteLists(BaseModel):
    ip_addr: str = None


class GetAPIWhiteLists(CreateAPIWhiteLists):
    id: int

    class Config:
        from_attributes = True
