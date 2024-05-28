from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.conn import db
from app.database.schema import Members, Course
from app.models import CustomResponse, CourseRegister, CoursePatch, CourseBase

router = APIRouter()

@router.get("/list", status_code=200, tags=["course"], response_model=CustomResponse)
async def get_course(
        name: Optional[str] = None,
        phone: Optional[str] = None,
        parent_phone: Optional[str] = None,
        class_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        session: Session = Depends(db.session)
):
    try:
        course_where = []
        members_where = []

        if name:
            members_where.append(Members.name.ilike(f"{name}%"))
        if phone:
            members_where.append(Members.phone == phone)
        if parent_phone:
            members_where.append(Members.parent_phone == parent_phone)
        if class_type:
            course_where.append(Course.class_type == class_type)
        if start_date:
            course_where.append(Course.start_date <= start_date)
        if end_date:
            course_where.append(Course.end_date >= end_date)

        # 수강정보 검색
        query = session.query(Course).filter(
            Course.deleted_at.is_(None),  # deleted_at이 null인 경우만 필터링
            *course_where
        ).join(Members).filter(
            Members.deleted_at.is_(None),
            *members_where
        )

        courses = query.all()

        course_infos = [
            {
                "id": course.id,
                "members_id": course.members_id,
                "start_date": course.start_date,
                "end_date": course.end_date,
                "session_count": course.session_count,
                "payment_amount": course.payment_amount,
                "member": {
                    "name": course.member.name,
                    "phone": course.member.phone,
                    "parent_phone": course.member.parent_phone,
                    "institution_name": course.member.institution_name,
                    "birth_day": course.member.birth_day,
                }
            } for course in courses
        ]

        return CustomResponse(
            result="success",
            result_msg="수강 정보 가져오기 성공",
            response={"result": course_infos}
        )
    except Exception as ve:
        raise HTTPException(status_code=404, detail="수강 정보 불러오기 실패")
    except HTTPException as e:
        # 예외 발생 시 로그 기록
        return CustomResponse(
            result="fail",
            result_msg=str(e.detail),
            response={"status_code": e.status_code}
        )

@router.post("/register", status_code=201, response_model=CustomResponse)
async def register_course(reg_info: CourseRegister, session: Session = Depends(db.session)):
    """
        `수강 정보 입력 API`\n
        reg_info: members_id, class_type, start_date, end_date, session_count, payment_amount
        :return:
        """
    try:
        if not reg_info.members_id or not reg_info.class_type or not reg_info.start_date or not reg_info.end_date or not reg_info.session_count or not reg_info.payment_amount:
            raise HTTPException(status_code=400, detail="필수값이 없습니다.")

        # 이름으로 회원 검색
        member = session.query(Members).filter(
            Members.id == reg_info.members_id,
            Members.deleted_at.is_(None)  # deleted_at이 null인 경우만 필터링
        ).first()

        if not member:
            raise HTTPException(status_code=404, detail="존재하지 않는 수강생 id")

        new_course = Course(
            members_id=reg_info.members_id,
            class_type=reg_info.class_type,
            start_date=reg_info.start_date,
            end_date=reg_info.end_date,
            session_count=reg_info.session_count,
            payment_amount=reg_info.payment_amount
        )
        session.add(new_course)
        session.commit()
        session.refresh(new_course)

        return CustomResponse(
            result="success",
            result_msg="수강 정보 입력 성공",
            response={"result": "True"}
        )

    except HTTPException as e:
        return CustomResponse(
            result="fail",
            result_msg=str(e.detail),
            response={"status_code": e.status_code}
        )

@router.patch("/{id}", status_code=200, response_model=CustomResponse)
def patch_course(id: int, reg_info: CoursePatch, session: Session = Depends(db.session)):
    """
        `수강생 정보 수정 API`\n
         id: 필수
    """

    try:
        if not id:
            raise HTTPException(status_code=404, detail="필수값 누락")

        # 이름으로 회원 검색
        course = session.query(Course).filter(
            Course.id == id,
            Course.deleted_at.is_(None)  # deleted_at이 null인 경우만 필터링
        ).first()

        if not course:
            raise HTTPException(status_code=404, detail="존재하지 않는 수강 id")

        if reg_info.class_type:
            course.class_type = reg_info.class_type

        if reg_info.start_date:
            course.start_date = reg_info.start_date

        if reg_info.end_date:
            course.end_date = reg_info.end_date

        if reg_info.session_count:
            course.session_count = reg_info.session_count

        if reg_info.payment_amount:
            course.payment_amount = reg_info.payment_amount

        session.commit()

        # 삭제된 회원 정보를 반환하지 않음
        return CustomResponse(
            result="success",
            result_msg="수강 정보 수정 성공",
            response={"result": "수강생 정보가 수정되었습니다."}
        )
    except HTTPException as e:
        # 예외 발생 시 로그 기록
        return CustomResponse(
            result="fail",
            result_msg=str(e.detail),  # HTTPException의 detail에 해당하는 메시지를 반환
            response={"status_code": e.status_code}
        )

@router.delete("/{id}", status_code=200, response_model=CustomResponse)
def del_course(id: int, session: Session = Depends(db.session)):
    """
        `수강생 정보 수정 API`\n
         id: 필수
    """

    try:
        if not id:
            raise HTTPException(status_code=404, detail="필수값 누락")

        # 이름으로 회원 검색
        course = session.query(Course).filter(
            Course.id == id,
            Course.deleted_at.is_(None)  # deleted_at이 null인 경우만 필터링
        ).first()

        if not course:
            raise HTTPException(status_code=404, detail="존재하지 않는 수강 id")

        course.deleted_at = datetime.now()
        session.commit()

        # 삭제된 회원 정보를 반환하지 않음
        return CustomResponse(
            result="success",
            result_msg="수강 정보 삭제 성공",
            response={"result": "수강생 정보가 삭제되었습니다."}
        )
    except HTTPException as e:
        # 예외 발생 시 로그 기록
        return CustomResponse(
            result="fail",
            result_msg=str(e.detail),  # HTTPException의 detail에 해당하는 메시지를 반환
            response={"status_code": e.status_code}
        )