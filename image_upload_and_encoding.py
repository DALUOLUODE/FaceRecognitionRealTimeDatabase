import os
import cv2
import face_recognition
import pickle
from supabase import create_client, Client

# 常量定义
SUPABASE_URL = "https://dudududu.supabase.co"  # Supabase 项目 URL
SUPABASE_SERVICE_KEY = "dudududu"  # Supabase 服务密钥
LOCAL_IMAGE_FOLDER = "Images"  # 本地图像文件夹
BUCKET_NAME = "imagesmeme"  # Supabase 存储桶名称
ENCODING_FILE = "encoded.pickle"  # 人脸编码保存文件

# 初始化 Supabase 客户端
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
print("Supabase client initialized successfully!")

def clear_bucket_files(bucket: str, folder: str) -> None:
    """清理 Supabase 存储桶中的指定文件夹内容"""
    try:
        files = supabase.storage.from_(bucket).list(path=folder)
        file_paths = [f"{folder}/{f['name']}" for f in files]
        if file_paths:
            supabase.storage.from_(bucket).remove(file_paths)
            print(f"Cleared existing files in {folder}/")
    except Exception as e:
        print(f"Failed to clear bucket files: {str(e)}")

def upload_images_to_supabase(image_paths: list) -> tuple[list, list]:
    """上传图像到 Supabase 并收集图像数据和学生 ID"""
    images = []
    student_ids = []

    for path in image_paths:
        file_path = os.path.join(LOCAL_IMAGE_FOLDER, path)
        print(f"Processing: {file_path}")

        # 读取图像
        img = cv2.imread(file_path)
        if img is None:
            print(f"Failed to read {file_path}")
            continue

        images.append(img)
        student_ids.append(os.path.splitext(path)[0])

        # 上传到 Supabase
        remote_path = f"{LOCAL_IMAGE_FOLDER}/{path}"
        try:
            with open(file_path, "rb") as file:
                supabase.storage.from_(BUCKET_NAME).upload(remote_path, file)
                print(f"Uploaded {file_path} to {remote_path}")
        except Exception as e:
            print(f"Failed to upload {file_path}: {str(e)}")
            continue

    print("All Student IDs:", student_ids)
    print("Total files uploaded:", len(images))
    return images, student_ids

def encode_faces(images: list) -> list:
    """对图像进行人脸编码"""
    encodings = []
    for img in images:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encoding = face_recognition.face_encodings(img_rgb)
        if encoding:  # 确保至少检测到一个面部
            encodings.append(encoding[0])
        else:
            print(f"No face detected in image")

    return encodings

def save_encodings(encodings: list, student_ids: list) -> None:
    """保存人脸编码和学生 ID 到 pickle 文件"""
    try:
        with open(ENCODING_FILE, "wb") as file:
            pickle.dump([encodings, student_ids], file)
        print("Encodings saved to", ENCODING_FILE)
    except Exception as e:
        print(f"Failed to save encodings: {str(e)}")

def main():
    """主函数：上传图像并生成人脸编码"""
    # 获取本地图像文件列表
    image_paths = os.listdir(LOCAL_IMAGE_FOLDER)
    print("Files to upload:", image_paths)

    # 清理存储桶
    clear_bucket_files(BUCKET_NAME, LOCAL_IMAGE_FOLDER)

    # 上传图像并收集数据
    images, student_ids = upload_images_to_supabase(image_paths)

    # 编码人脸
    print("Starting face encoding...")
    encodings = encode_faces(images)
    print("Encoding finished")

    # 保存编码
    save_encodings(encodings, student_ids)

if __name__ == "__main__":
    main()