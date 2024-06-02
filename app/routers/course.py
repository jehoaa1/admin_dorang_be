from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.conn import db
from app.database.schema import Members, Course, ClassBooking
from app.models import CustomResponse, CourseRegister, CoursePatch, CourseBase
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import aliased
from app.common.consts import CLASS_TYPE
from fastapi import Query

router = APIRouter()

from typing import Optional

@router.get("/list", status_code=200, tags=["course"], response_model=CustomResponse)
async def get_course(
        id: Optional[int] = None,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        parent_phone: Optional[str] = None,
        class_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = Query(1, ge=1),  # 기본 페이지 번호는 1
        per_page: int = Query(10, ge=1, le=100),  # 페이지당 항목 수 제한 (10~100)
        session: Session = Depends(db.session)
):
    try:
        course_alias = aliased(Course)
        members_alias = aliased(Members)

        course_where = []
        members_where = []

        if id:
            course_where.append(course_alias.id == id)
        if name:
            members_where.append(members_alias.name.ilike(f"%{name}%"))
        if phone:
            members_where.append(members_alias.phone == phone)
        if parent_phone:
            members_where.append(members_alias.parent_phone == parent_phone)
        if class_type:
            course_where.append(course_alias.class_type == class_type)
        if start_date and end_date:
            course_where.append(
                or_(
                    and_(course_alias.start_date >= start_date, course_alias.start_date <= end_date),
                    and_(course_alias.end_date >= start_date, course_alias.end_date <= end_date),
                    and_(course_alias.start_date <= start_date, course_alias.end_date >= end_date)
                )
            )
        else:
            if start_date:
                course_where.append(course_alias.start_date >= start_date)
            if end_date:
                course_where.append(course_alias.end_date <= end_date)

        # 수강정보 검색
        query = session.query(course_alias).filter(
            course_alias.deleted_at.is_(None),  # deleted_at이 null인 경우만 필터링
            *course_where
        ).join(members_alias).filter(
            members_alias.deleted_at.is_(None),
            *members_where
        )

        # 페이징 적용
        total_count = query.count()  # 전체 결과 수 계산
        # 결과 정렬
        query = query.order_by(desc(course_alias.id))
        courses = query.offset((page - 1) * per_page).limit(per_page).all()

        course_infos = []
        for course in courses:
            course_info = {
                "id": course.id,
                "members_id": course.members_id,
                "start_date": course.start_date,
                "end_date": course.end_date,
                "session_count": course.session_count,
                "payment_amount": course.payment_amount,
                "payment_date": course.payment_date,
                "class_type": course.class_type,
                "class_type_txt": CLASS_TYPE.get(course.class_type, "Unknown class"),
                "member": {
                    "name": course.member.name,
                    "phone": course.member.phone,
                    "parent_phone": course.member.parent_phone,
                    "institution_name": course.member.institution_name,
                    "birth_day": course.member.birth_day,
                },
                "class_booking": []  # 클래스 예약 정보를 저장할 빈 리스트
            }

            # 해당 코스의 클래스 예약 정보 가져오기
            class_bookings = session.query(ClassBooking).filter(
                ClassBooking.course_id == course.id,
                ClassBooking.deleted_at.is_(None)  # deleted_at이 null인 경우만 필터링
            ).all()

            for class_booking in class_bookings:
                class_booking_info = {
                    "id": class_booking.id,
                    "reservation_date": class_booking.reservation_date,
                    "enrollment_status": class_booking.enrollment_status
                }
                course_info["class_booking"].append(class_booking_info)

            course_infos.append(course_info)

        return CustomResponse(
            result="success",
            result_msg="수강 정보 가져오기 성공",
            response={"result": course_infos, "total_count": total_count}
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


@router.get("/remain/session-count/list", status_code=200, tags=["course"], response_model=CustomResponse)
async def get_course(
        id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        session: Session = Depends(db.session)
):
    try:
        course_alias = aliased(Course)
        members_alias = aliased(Members)
        class_booking_alias = aliased(ClassBooking)

        course_where = []

        if id:
            course_where.append(course_alias.id == id)

        if start_date and end_date:
            course_where.append(
                or_(
                    and_(course_alias.start_date >= start_date, course_alias.start_date <= end_date),
                    and_(course_alias.end_date >= start_date, course_alias.end_date <= end_date),
                    and_(course_alias.start_date <= start_date, course_alias.end_date >= end_date)
                )
            )
        else:
            if start_date:
                course_where.append(course_alias.start_date >= start_date)
            if end_date:
                course_where.append(course_alias.end_date <= end_date)

        # 수강정보 검색
        subq = session.query(
            class_booking_alias.course_id,
            func.count(class_booking_alias.course_id).label("use_num")
        ).filter(
            class_booking_alias.enrollment_status.in_([1, 2]),
            class_booking_alias.deleted_at.is_(None)
        ).group_by(
            class_booking_alias.course_id
        ).subquery()

        query = session.query(course_alias).filter(
            course_alias.deleted_at.is_(None),
            *course_where
        ).join(
            members_alias,
            course_alias.members_id == members_alias.id
        ).outerjoin(
            subq,
            course_alias.id == subq.c.course_id
        ).filter(
            or_(course_alias.session_count > subq.c.use_num, subq.c.use_num.is_(None))
        )

        courses = query.all()

        course_infos = []
        for course in courses:
            course_info = {
                "id": course.id,
                "members_id": course.members_id,
                "start_date": course.start_date,
                "end_date": course.end_date,
                "session_count": course.session_count,
                "payment_amount": course.payment_amount,
                "payment_date": course.created_at,
                "class_type": course.class_type,
                "class_type_txt": CLASS_TYPE.get(course.class_type, "Unknown class"),
                "member": {
                    "name": course.member.name,
                    "phone": course.member.phone,
                    "parent_phone": course.member.parent_phone,
                    "institution_name": course.member.institution_name,
                    "birth_day": course.member.birth_day,
                }
            }
            course_infos.append(course_info)

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
        if not reg_info.members_id or not reg_info.class_type or not reg_info.start_date or not reg_info.end_date or not reg_info.session_count or not reg_info.payment_date or not reg_info.payment_amount:
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
            payment_date=reg_info.payment_date,
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

        if reg_info.payment_date:
            course.payment_date = reg_info.payment_date

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