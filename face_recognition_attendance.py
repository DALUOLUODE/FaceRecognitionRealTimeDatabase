from datetime import datetime
import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
from supabase import create_client, Client

# 常量定义
SUPABASE_URL = "https://dudu.supabase.co"  # Supabase 项目 URL
SUPABASE_SERVICE_KEY = "dududu"  # Supabase 服务密钥
BUCKET_NAME = "imagesmeme"  # Supabase 存储桶名称
IMAGE_FOLDER = "Images"  # 图像存储文件夹
MODE_FOLDER = "Resources/Modes"  # 模式图像文件夹
BACKGROUND_IMAGE_PATH = "Resources/background.png"  # 背景图像路径
ENCODING_FILE = "encoded.pickle"  # 人脸编码文件
ATTENDANCE_INTERVAL_SECONDS = 30  # 考勤间隔时间（秒）

# 初始化 Supabase 客户端
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
print("Supabase client initialized successfully!")

# 初始化摄像头
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # 设置宽度
cap.set(4, 480)  # 设置高度

# 加载背景图像
background_frame = cv2.imread(BACKGROUND_IMAGE_PATH)
if background_frame is None:
    raise FileNotFoundError(f"Background image not found at {BACKGROUND_IMAGE_PATH}. Please check the file path and ensure the file exists.")

# 加载模式图像
mode_images = [cv2.imread(os.path.join(MODE_FOLDER, path)) for path in os.listdir(MODE_FOLDER)]
if not mode_images or any(img is None for img in mode_images):
    raise FileNotFoundError(f"Mode images not found or corrupted in {MODE_FOLDER}. Please verify the directory and files.")

# 加载已编码的人脸数据
print("Loading encoded file...")
try:
    with open(ENCODING_FILE, "rb") as file:
        encoded_data = pickle.load(file)
    print("Loaded encoded file")
    encoded_faces, student_ids = encoded_data  # 解包编码人脸和学生 ID
except FileNotFoundError:
    raise FileNotFoundError(f"Encoded file not found at {ENCODING_FILE}. Please run the encoding script first.")
except Exception as e:
    raise Exception(f"Failed to load encoded file: {str(e)}")

# 初始化状态变量
current_mode = 0  # 模式索引 (0: 待机, 1: 加载, 2: 显示信息, 3: 间隔)
attendance_counter = 0  # 计时器
current_student_id = -1  # 当前识别的学生 ID
student_info = None  # 学生信息
student_image = None  # 学生图像

def fetch_student_info(student_id: str) -> dict:
    """从 Supabase 获取学生信息"""
    try:
        response = supabase.table("students").select("*").eq("id", student_id).single().execute()
        return response.data
    except Exception as e:
        print(f"Failed to fetch student info for ID {student_id}: {str(e)}")
        return None

def load_student_image(student_id: str) -> np.ndarray:
    """从 Supabase 存储桶下载学生图像"""
    remote_path = f"{IMAGE_FOLDER}/{student_id}.png"
    try:
        image_data = supabase.storage.from_(BUCKET_NAME).download(remote_path)
        return cv2.imdecode(np.frombuffer(image_data, dtype=np.uint8), cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"Failed to download image for ID {student_id}: {str(e)}")
        return None

def update_attendance(student_id: str) -> None:
    """更新学生的考勤信息，包括总次数和最后出勤时间"""
    global current_mode
    try:
        # 获取当前学生信息
        data = fetch_student_info(student_id)
        if not data:
            return

        # 检查上次出勤时间
        last_attendance = datetime.strptime(data["last_attendance_time"], "%Y-%m-%d %H:%M:%S")
        elapsed_seconds = (datetime.now() - last_attendance).total_seconds()

        if elapsed_seconds > ATTENDANCE_INTERVAL_SECONDS:
            # 更新考勤次数
            data["total_attendance"] += 1
            supabase.table("students").update({"total_attendance": data["total_attendance"]}).eq("id", student_id).execute()
            # 更新最后出勤时间
            supabase.table("students").update({"last_attendance_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}).eq("id", student_id).execute()
            print(f"Updated attendance for ID {student_id}: {data['total_attendance']} times")
        else:
            current_mode = 3  # 设置为间隔模式
    except Exception as e:
        print(f"Error updating attendance for ID {student_id}: {str(e)}")

def display_student_info(frame: np.ndarray) -> None:
    """在背景帧上显示学生信息"""
    if student_info is None or student_image is None:
        return

    # 显示学生信息
    cv2.putText(frame, str(student_info["total_attendance"]), (861, 125),
                cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
    cv2.putText(frame, str(student_info["major"]), (1006, 550),
                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, str(student_info["id"]), (1006, 493),
                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, str(student_info["standing"]), (910, 625),
                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
    cv2.putText(frame, str(student_info["year"]), (1025, 625),
                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
    cv2.putText(frame, str(student_info["starting_year"]), (1125, 625),
                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

    # 计算姓名文本的偏移量以居中显示
    (w, h), _ = cv2.getTextSize(str(student_info["name"]), cv2.FONT_HERSHEY_COMPLEX, 1, 1)
    offset = (414 - w) // 2
    cv2.putText(frame, str(student_info["name"]), (808 + offset, 445),
                cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

    # 显示学生图像
    frame[175:175 + 216, 909:909 + 216] = student_image

def main():
    """主函数：运行实时人脸识别考勤系统"""
    global current_mode, attendance_counter, current_student_id, student_info, student_image, background_frame

    while True:
        success, frame = cap.read()
        if not success:
            print("Failed to capture video frame")
            break

        # 调整帧大小并转换颜色空间
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # 检测人脸和编码
        current_face_locations = face_recognition.face_locations(small_frame)
        current_face_encodings = face_recognition.face_encodings(small_frame, current_face_locations) if current_face_locations else []

        # 将摄像头帧叠加到背景上
        background_frame[162:162 + 480, 55:55 + 640] = frame
        background_frame[44:44 + 633, 808:808 + 414] = mode_images[current_mode]

        if current_face_locations:
            for face_encoding, face_loc in zip(current_face_encodings, current_face_locations):
                # 比较人脸
                matches = face_recognition.compare_faces(encoded_faces, face_encoding)
                face_distances = face_recognition.face_distance(encoded_faces, face_encoding)
                match_index = np.argmin(face_distances)

                if matches[match_index]:
                    # 绘制边界框
                    y1, x2, y2, x1 = [coord * 4 for coord in face_loc]
                    bbox = (55 + x1, 162 + y1, x2 - x1, y2 - y1)
                    background_frame = cvzone.cornerRect(background_frame, bbox, rt=0)

                    current_student_id = student_ids[match_index]
                    if attendance_counter == 0:
                        cvzone.putTextRect(background_frame, "Loading", (275, 400))
                        cv2.imshow("Attendance System", background_frame)
                        cv2.waitKey(1)
                        attendance_counter = 1
                        current_mode = 1

            if attendance_counter > 0:
                if attendance_counter == 1:
                    # 加载学生信息和图像
                    student_info = fetch_student_info(current_student_id)
                    student_image = load_student_image(current_student_id)

                if current_mode != 3:  # 非间隔模式
                    if 10 < attendance_counter < 20:
                        current_mode = 2  # 显示信息模式

                    background_frame[44:44 + 633, 808:808 + 414] = mode_images[current_mode]

                    if attendance_counter <= 10:
                        display_student_info(background_frame)

                    attendance_counter += 1

                    if attendance_counter > 20:
                        update_attendance(current_student_id)  # 更新考勤
                        attendance_counter = 0
                        current_mode = 0
                        student_info = None
                        student_image = None
                        background_frame[44:44 + 633, 808:808 + 414] = mode_images[current_mode]
        else:
            current_mode = 0
            attendance_counter = 0

        cv2.imshow("Attendance System", background_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()