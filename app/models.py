from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Any
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

class MemberPatch(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    parent_phone: Optional[str] = None
    institution_name: Optional[str] = None
    birth_day: Optional[datetime] = None

class CourseRegister(BaseModel):
    members_id: int
    class_type: str
    start_date: datetime
    end_date: datetime
    session_count: int
    payment_amount: int

class CoursePatch(BaseModel):
    members_id: Optional[int] = None
    class_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    session_count: Optional[int] = None
    payment_amount: Optional[int] = None

class ClassBookingRegister(BaseModel):
    course_id: int
    reservation_date: datetime
    enrollment_status: str

class ClassBookingPatch(BaseModel):
    reservation_date: Optional[datetime] = None
    enrollment_status: Optional[str] = None


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

class UserToken(BaseModel):
    id: int
    email: Optional[str] = None
    name: Optional[str] = None
    sns_type: Optional[str] = None

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
    class_type: str
    start_date: datetime
    end_date: datetime
    session_count: int
    payment_amount: int

    class Config:
        from_attributes = True

class ClassBookingBase(BaseModel):
    id: int
    course_id: int
    reservation_date: datetime
    enrollment_status: str

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
