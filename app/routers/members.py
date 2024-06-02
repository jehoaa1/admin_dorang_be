from datetime import datetime, time
from fastapi import APIRouter, Depends, HTTPException
import logging
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.database.conn import db
from app.database.schema import Members
from app.models import MemberRegister, MemberPatch, CustomResponse, MembersBase, CourseBase
from typing import Optional
from fastapi import Query

router = APIRouter()
@router.get("/list", status_code=200, response_model=CustomResponse)
def get_member(
    id: Optional[int] = None,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    parent_phone: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),  # 기본 페이지 번호는 1
    per_page: int = Query(10, ge=1, le=100),  # 페이지당 항목 수 제한 (10~100)
    session: Session = Depends(db.session)
):
    try:
        try:
            # 이름으로 회원 검색
            query = session.query(Members).filter(
                Members.deleted_at.is_(None)  # deleted_at이 null인 경우만 필터링
            )
            if id:
                query = query.filter(Members.id == id)

            if name:
                query = query.filter(Members.name.ilike(f"%{name}%"))

            if phone:
                query = query.filter(Members.phone.ilike(f"%{phone}%"))

            if parent_phone:
                query = query.filter(Members.parent_phone.ilike(f"%{parent_phone}%"))

            if start_date:
                query = query.filter(Members.created_at >= start_date)

            if end_date:
                end_date = datetime.combine(end_date.date(), time.max)
                query = query.filter(Members.created_at <= end_date)

            # 페이징을 적용하여 쿼리 실행
            total_count = query.count()
            # 결과 정렬
            query = query.order_by(desc(Members.id))
            members = query.offset((page - 1) * per_page).limit(per_page).all()

            # 결과를 파이썬 객체로 변환
            users_response = []

            for member in members:
                member_info = MembersBase.from_orm(member)
                member_courses = []
                for course in member.courses:
                    if course.deleted_at is None:  # 삭제되지 않은 수강 정보만 추가
                        member_courses.append(CourseBase.from_orm(course))
                users_response.append({"member": member_info, "courses": member_courses})

            return CustomResponse(
                result="success",
                result_msg="회원 정보 및 수강 정보 가져오기 성공",
                response={"result": users_response, "total_count": total_count}
            )
        except Exception as ve:
            logging.error(f"Validation error: {ve}")
            raise HTTPException(status_code=404, detail="회원 정보 및 수강 정보 불러오기 실패")
    except HTTPException as e:
        # 예외 발생 시 로그 기록
        logging.error(f"Error occurred: {e}")
        return CustomResponse(
            result="fail",
            result_msg=str(e.detail),
            response={"status_code": e.status_code}
        )

@router.post("/register", status_code=201, response_model=CustomResponse)
async def register(reg_info: MemberRegister, session: Session = Depends(db.session)):
    """
    `수강생 정보 입력 API`\n
    reg_info: name, phone, parent_phone, institution_name, birth_day
    :return:
    """
    try:
        if not reg_info.name or not reg_info.parent_phone or not reg_info.birth_day:
            raise HTTPException(status_code=400, detail="이름, 부모 연락처, 생년월일은 필수입니다.")

        try:
            # 수강생 정보 입력
            new_member = Members(
                name=reg_info.name,
                phone=reg_info.phone,
                parent_phone=reg_info.parent_phone,
                institution_name=reg_info.institution_name,
                birth_day=reg_info.birth_day
            )
            session.add(new_member)
            session.commit()
            session.refresh(new_member)

        except Exception as ve:
            logging.error(f"Validation error: {ve}")
            session.rollback()
            raise HTTPException(status_code=500, detail="수강정보 저장실패")

        return CustomResponse(
            result="success",
            result_msg="수강생 정보 입력 성공",
            response={"result": "True"}
        )
    except HTTPException as e:
        logging.error(f"Error occurred: {str(e)}")
        return CustomResponse(
            result="fail",
            result_msg=str(e.detail),
            response={"status_code": e.status_code}
        )
@router.patch("/{id}", status_code=200, response_model=CustomResponse)
def patch_member(id: int, reg_info: MemberPatch, session: Session = Depends(db.session)):
    """
        `수강생 정보 수정 API`\n
         id: 필수
    """

    try:
        if not id:
            raise HTTPException(status_code=404, detail="필수값 누락")

        # 이름으로 회원 검색
        member = session.query(Members).filter(
            Members.id == id,
            Members.deleted_at.is_(None)  # deleted_at이 null인 경우만 필터링
        ).first()

        if not member:
            raise HTTPException(status_code=404, detail="존재하지 않는 수강생 id")

        if reg_info.name:
            member.name = reg_info.name
        if reg_info.phone:
            member.phone = reg_info.phone
        if reg_info.parent_phone:
            member.parent_phone = reg_info.parent_phone
        if reg_info.institution_name:
            member.institution_name = reg_info.institution_name
        if reg_info.birth_day:
            member.birth_day = reg_info.birth_day

        session.commit()

        # 삭제된 회원 정보를 반환하지 않음
        return CustomResponse(
            result="success",
            result_msg="수강생 정보 수정 성공",
            response={"result": "수강생 정보가 수정되었습니다."}
        )
    except HTTPException as e:
        # 예외 발생 시 로그 기록
        logging.error(f"Error occurred: {e}")
        return CustomResponse(
            result="fail",
            result_msg=str(e.detail),  # HTTPException의 detail에 해당하는 메시지를 반환
            response={"status_code": e.status_code}
        )
@router.delete("/{id}", status_code=200, response_model=CustomResponse)
def del_member(id: int, session: Session = Depends(db.session)):
    """
        `수강생 삭제 (물리삭제 X, 논리삭제O) API`\n
         id: 필수
        :return:
    """

    try:
        if not id:
            raise HTTPException(status_code=404, detail="필수값 누락")

        # 이름으로 회원 검색
        member = session.query(Members).filter(
            Members.id == id,
            Members.deleted_at.is_(None)  # deleted_at이 null인 경우만 필터링
        ).first()

        if not member:
            raise HTTPException(status_code=404, detail="존재하지 않는 수강생 id")

        member.deleted_at = datetime.now()
        session.commit()

        # 삭제된 회원 정보를 반환하지 않음
        return CustomResponse(
            result="success",
            result_msg="수강생 정보 삭제 성공",
            response={"result": "수강생 정보가 삭제되었습니다."}
        )
    except HTTPException as e:
        # 예외 발생 시 로그 기록
        logging.error(f"Error occurred: {e}")
        return CustomResponse(
            result="fail",
            result_msg=str(e.detail),  # HTTPException의 detail에 해당하는 메시지를 반환
            response={"status_code": e.status_code}
        )