from fastapi import APIRouter, Depends, HTTPException
from app.models import ClassBookingRegister, ClassBookingPatch, CustomResponse, MembersBase, CourseBase, ClassBookingBase
from datetime import datetime, date
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database.schema import ClassBooking, Course, Members
from app.database.conn import db
from typing import Optional

router = APIRouter()

@router.get("/list", status_code=200, response_model=CustomResponse)
def get_class_booking(start_date: Optional[date] = None, end_date: Optional[date] = None, member_id: Optional[int] = None, member_name: Optional[str] = None, session: Session = Depends(db.session)):
    """
        `수강생 정보 API`\n
         name: 첫 글자는 무조건 동일해야함.
        :return:
        """
    try:
        try:
            # 이름으로 회원 검색
            query = session.query(ClassBooking).filter(
                ClassBooking.deleted_at.is_(None)  # deleted_at이 null인 경우만 필터링
            ).join(Course).filter(
                Course.deleted_at.is_(None),
            ).join(Members).filter(
                Members.deleted_at.is_(None)
            )

            if start_date:
                query = query.filter(func.date(ClassBooking.reservation_date) >= start_date)

            if end_date:
                query = query.filter(func.date(ClassBooking.reservation_date) <= end_date)

            if member_name:
                query = query.filter(Members.name.ilike(f"{member_name}%"))

            if member_id:
                query = query.filter(Members.id == member_id)

            class_booking = query.all()

            users_response = [
                {
                    "id": cb.id,
                    "reservation_date": cb.reservation_date,
                    "enrollment_status": cb.enrollment_status,
                    "course": {
                        "id": cb.course.id,
                        "class_type": cb.course.class_type,
                        "payment_amount": cb.course.payment_amount
                    },
                    "member": {
                        "name": cb.course.member.name,
                        "phone": cb.course.member.phone,
                        "parent_phone": cb.course.member.parent_phone
                    }
                } for cb in class_booking
            ]

            return CustomResponse(
                result="success",
                result_msg="회원 정보 및 수강 정보 가져오기 성공",
                response={"result": users_response}
            )
        except Exception as ve:
            raise HTTPException(status_code=404, detail="회원 정보 및 수강 정보 불러오기 실패")
    except HTTPException as e:
        # 예외 발생 시 로그 기록
        return CustomResponse(
            result="fail",
            result_msg=str(e.detail),
            response={"status_code": e.status_code}
        )

@router.post("/register", status_code=201, response_model=CustomResponse)
async def register_class_booking(reg_info: ClassBookingRegister, session: Session = Depends(db.session)):
    """
        `수강 정보 입력 API`\n
        reg_info: members_id, class_type, start_date, end_date, session_count, payment_amount
        :return:
        """
    try:
        if not reg_info.course_id or not reg_info.reservation_date or not reg_info.enrollment_status:
            raise HTTPException(status_code=400, detail="필수값이 없습니다.")

        # 수강 목록 검색
        course = session.query(Course).filter(
            Course.id == reg_info.course_id,
            Course.deleted_at.is_(None)  # deleted_at이 null인 경우만 필터링
        ).first()

        if not course:
            raise HTTPException(status_code=404, detail="존재하지 않는 수강 id")

        #수강 횟수 확인
        count_class_booking = session.query(func.count(ClassBooking.id)).filter(
            ClassBooking.course_id == reg_info.course_id,
            ClassBooking.enrollment_status != "3",
            ClassBooking.deleted_at.is_(None)
        ).scalar()

        session_count = course.session_count

        if session_count <= count_class_booking:
            raise HTTPException(status_code=403, detail=f"완료 된 수강횟수(완료 수강 횟수: {count_class_booking})")

        # 중복 수강 안되도록 확인
        count_class_booking_duplication = session.query(func.count(ClassBooking.id)).filter(
            ClassBooking.course_id == reg_info.course_id,
            func.date(ClassBooking.reservation_date) == reg_info.reservation_date.strftime(
                '%Y-%m-%d'),
            ClassBooking.enrollment_status != "3",
            ClassBooking.deleted_at.is_(None)
        ).scalar()

        if count_class_booking_duplication >= 1:
            raise HTTPException(status_code=403, detail=f"중복 된 수강 날짜")


        new_class_booking = ClassBooking(
            course_id=reg_info.course_id,
            reservation_date=reg_info.reservation_date.strftime('%Y-%m-%d %H:%M:00'),
            enrollment_status=reg_info.enrollment_status
        )
        session.add(new_class_booking)
        session.commit()

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
def patch_class_booking(id: int, reg_info: ClassBookingPatch, session: Session = Depends(db.session)):
    """
        `수강생 정보 수정 API`\n
         id: 필수
    """

    try:
        if not id:
            raise HTTPException(status_code=404, detail="필수값 누락")

        # 이름으로 회원 검색
        classBooking = session.query(ClassBooking).filter(
            ClassBooking.id == id,
            ClassBooking.deleted_at.is_(None)  # deleted_at이 null인 경우만 필터링
        ).first()

        if not classBooking:
            raise HTTPException(status_code=404, detail="존재하지 않는 수강 id")

        if reg_info.reservation_date:
            classBooking.reservation_date = reg_info.reservation_date

        if reg_info.enrollment_status:
            classBooking.enrollment_status = reg_info.enrollment_status

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
def del_class_booking(id: int, session: Session = Depends(db.session)):
    """
        `수강생 정보 수정 API`\n
         id: 필수
    """

    try:
        if not id:
            raise HTTPException(status_code=404, detail="필수값 누락")

        # 이름으로 회원 검색
        classBooking = session.query(ClassBooking).filter(
            ClassBooking.id == id,
            ClassBooking.deleted_at.is_(None)  # deleted_at이 null인 경우만 필터링
        ).first()

        if not classBooking:
            raise HTTPException(status_code=404, detail="존재하지 않는 수강 id")

        classBooking.deleted_at = datetime.now()
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