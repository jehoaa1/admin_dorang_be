from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import pickle
import face_recognition
import numpy as np
import cv2

router = APIRouter()

# 얼굴 인식을 위한 변수 초기화
known_face_encodings = []
known_face_names = []

# 미리 저장된 얼굴 데이터 파일 경로
known_faces_file = "known_faces.dat"


# 저장된 얼굴 데이터를 로드하는 함수
def load_known_faces():
    global known_face_encodings, known_face_names
    try:
        with open(known_faces_file, "rb") as f:
            known_face_encodings, known_face_names = pickle.load(f)
    except FileNotFoundError:
        # 파일이 없는 경우 초기화
        known_face_encodings = []
        known_face_names = []


# 초기에 얼굴 데이터 로드
load_known_faces()


# 얼굴 데이터를 파일로 저장하는 함수
def save_known_faces():
    with open(known_faces_file, "wb") as f:
        pickle.dump((known_face_encodings, known_face_names), f)


# 얼굴 데이터 추가 함수
def add_face_encoding(face_encoding, name):
    known_face_encodings.append(face_encoding)
    known_face_names.append(name)
    save_known_faces()

# 두 얼굴 인코딩 간의 거리를 백분율로 계산하는 함수
def calculate_similarity_percent(face_encoding1, face_encoding2):
    distance = face_recognition.face_distance([face_encoding1], face_encoding2)
    similarity_percent = (1 - distance[0]) * 100
    return similarity_percent


# 얼굴 데이터 추가 API 엔드포인트
@router.post("/add_face/")
async def add_face(name: str, request: UploadFile = File(...)):
    try:
        face_img = await request.read()  # UploadFile에서 바로 데이터를 읽음

        # OpenCV를 이용하여 이미지 디코딩
        image_array = np.asarray(bytearray(face_img), dtype=np.uint8)
        frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Could not decode image")

        # 얼굴 인식을 위해 RGB로 변환
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 얼굴 위치 찾기
        face_locations = face_recognition.face_locations(rgb_frame)

        # 각 얼굴 인코딩과 이름 추가
        for face_location in face_locations:
            top, right, bottom, left = face_location
            face_encoding = face_recognition.face_encodings(rgb_frame, [face_location])[0]
            add_face_encoding(face_encoding, name)

        return JSONResponse(content={"message": f"Added face '{name}' successfully."})

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 얼굴 인식 API 엔드포인트
@router.post("/recognize_face/")
async def recognize_face(request: UploadFile = File(...)):
    try:
        face_img = await request.read()  # UploadFile에서 바로 데이터를 읽음

        # OpenCV를 이용하여 이미지 디코딩
        image_array = np.asarray(bytearray(face_img), dtype=np.uint8)
        frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Could not decode image")

        # 얼굴 인식을 위해 RGB로 변환
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 얼굴 위치 찾기
        face_locations = face_recognition.face_locations(rgb_frame)

        # 인식된 얼굴들의 이름 리스트
        recognized_faces = []

        # 각 얼굴 인코딩과 기존 데이터 비교하여 이름 추론
        for face_location in face_locations:
            top, right, bottom, left = face_location
            face_encoding = face_recognition.face_encodings(rgb_frame, [face_location])[0]

            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "인식못함"

            # 거리 계산 후 가장 가까운 얼굴 선택
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                similarity_percent = calculate_similarity_percent(known_face_encodings[best_match_index], face_encoding)
                recognized_faces.append({"name": name, "similarity_percent": similarity_percent})
            else:
                recognized_faces.append({"name": name, "similarity_percent": 0.0})  # 일치하는 얼굴이 없을 경우

        return JSONResponse(content={"recognized_faces": recognized_faces})

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
