import cv2
import face_recognition
import pickle
import os
from supabase import create_client, Client


# Supabase 项目的基本信息
SUPABASE_URL = "https://hahahhaha.supabase.co"  # 替换为你的 Project URL
SUPABASE_SERVICE_KEY = "hahahaha"          # 替换为你的 service_role 密钥

# 初始化 Supabase 客户端
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# 测试是否连接成功（可选）
print("Supabase client initialized successfully!")

Folder='Images'
pathList=os.listdir(Folder)
Students=[]
studentsId=[]
bucket_name="imagesmeme"

print("Files to upload:", pathList)

# 可选：清理存储桶
files = supabase.storage.from_(bucket_name).list(path=f"{Folder}")
file_paths = [f"{Folder}/{f['name']}" for f in files]
if file_paths:
    supabase.storage.from_(bucket_name).remove(file_paths)
    print(f"Cleared existing files in {Folder}/")

# 上传文件
for path in pathList:
    fileName = os.path.join(Folder, path)
    print(f"Processing: {fileName}")

    # 读取图像
    img = cv2.imread(fileName)
    if img is None:
        print(f"Failed to read {fileName}")
        continue
    Students.append(img)

    # 提取学生 ID
    studentsId.append(os.path.splitext(path)[0])

    # 上传文件
    remote_path = f"{Folder}/{path}"
    try:
        with open(fileName, "rb") as file:
            response = supabase.storage.from_(bucket_name).upload(remote_path, file)
            print(f"Uploaded {fileName} to {remote_path}")
    except Exception as e:
        print(f"Failed to upload {fileName}: {str(e)}")
        continue

print("All Students IDs:", studentsId)
print("Total files uploaded:", len(Students))

def findEncodings(Students):
    encodings=[]
    for student in Students:
        student=cv2.cvtColor(student,cv2.COLOR_BGR2RGB)
        encoding = face_recognition.face_encodings(student)[0]
        encodings.append(encoding)

    return encodings

print("start encoding...")
encodeStudents=findEncodings(Students)
encodeStudents_Id=[encodeStudents,studentsId]
print("encoding finished")
file=open("encoded.pickle","wb")
pickle.dump(encodeStudents_Id,file)
file.close()
print("file saved")