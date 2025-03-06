from datetime import datetime
import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
from PIL.ImageChops import offset
from supabase import create_client, Client


# Supabase 项目的基本信息
SUPABASE_URL = "https://lheqmfatlqoulgavjlan.supabase.co"  # 替换为你的 Project URL
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxoZXFtZmF0bHFvdWxnYXZqbGFuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MDkyMDkyNSwiZXhwIjoyMDU2NDk2OTI1fQ.jvDO0Rm-HLCyNDTVbvSfqY6ckvTB_cyr-SI8p8_vFxs"          # 替换为你的 service_role 密钥

# 初始化 Supabase 客户端
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# 测试是否连接成功（可选）
print("Supabase client initialized successfully!")

cap=cv2.VideoCapture(0)
cap.set(3,640)
cap.set(4,480)

frameBackground=cv2.imread('Resources/background.png')

Folder='Resources/Modes'
bucket_name="imagesmeme"
remote_path = f"Images/{id}.png"
pathList=os.listdir(Folder)
Modes=[]
imgStudent=[]
for path in pathList:
    Modes.append(cv2.imread(os.path.join(Folder,path)))

print("loading encoded file...")
file=open('encoded.pickle','rb')
encodeStudents_Id=pickle.load(file)
file.close()
print("loaded encoded file")

encodeStudents,studentsId=encodeStudents_Id
print(studentsId)

mode_Type=0
Counter=0
id=-1

while(True):
    success,frame=cap.read()
    frameSmall=cv2.resize(frame,(0,0),None,0.25,0.25)
    frameSmall=cv2.cvtColor(frameSmall,cv2.COLOR_BGR2RGB)

    faceCurFrame=face_recognition.face_locations(frameSmall)
    encodeCurFrame=face_recognition.face_encodings(frameSmall,faceCurFrame)

    frameBackground[162:162+480,55:55+640]=frame
    frameBackground[44:44+633,808:808+414]=Modes[mode_Type]

    if faceCurFrame:

        for encodeFace,faceLoc in zip(encodeCurFrame,faceCurFrame):
            matches=face_recognition.compare_faces(encodeStudents,encodeFace)
            faceDis=face_recognition.face_distance(encodeStudents,encodeFace)
            # print("matches" ,matches)
            # print("faceDis",faceDis)

            matchIndex=np.argmin(faceDis)
            if(matches[matchIndex]):
                y1,x2,y2,x1=faceLoc
                y1,x2,y2,x1=y1*4,x2*4,y2*4,x1*4
                bbox=55+x1,162+y1,x2-x1,y2-y1
                frameBackground=cvzone.cornerRect(frameBackground,bbox,rt=0)
                id=studentsId[matchIndex]
                if Counter==0:
                    cvzone.putTextRect(frameBackground,"Loading",(275,400))
                    cv2.imshow('frameBackground',frameBackground)
                    # if cv2.waitKey(1) & 0xFF == ord('q'):
                    #     break
                    cv2.waitKey(1)
                    Counter=1
                    mode_Type=1

        if Counter!=0:
            # get the data
            if Counter==1:
                # 获取学生信息
                try:
                    studentInfo = supabase.table("students").select("*").eq("id", id).single().execute()
                    print("Student Info:", studentInfo.data)
                except Exception as e:
                    print(f"Failed to fetch student info for id {id}: {str(e)}")

                # 下载图像
                remote_path = f"Images/{id}.png"  # 动态生成路径，假设与上传一致
                print(f"Downloading image from: {remote_path}")
                try:
                    array = supabase.storage.from_(bucket_name).download(remote_path)
                    imgStudent = cv2.imdecode(np.frombuffer(array, dtype=np.uint8), cv2.COLOR_BGRA2BGR)
                    if imgStudent is None:
                        print(f"Failed to decode image for id {id}")
                except Exception as e:
                    print(f"Failed to download image {remote_path}: {str(e)}")
                    imgStudent = None

                if imgStudent is not None:
                    datetimeObject=datetime.strptime(studentInfo.data['last_attendance_time'],
                                                    "%Y-%m-%d %H:%M:%S")
                    secondsElapsed=(datetime.now()-datetimeObject).total_seconds()
                    print(secondsElapsed)
                    if secondsElapsed > 30:
                        # 更新信息
                        studentInfo = supabase.table("students").select("*").eq("id", id).single().execute()
                        studentInfo.data['total_attendance'] += 1
                        supabase.table("students").update({"total_attendance": studentInfo.data['total_attendance']}).eq("id",id).execute()
                        supabase.table("students").update({"last_attendance_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}).eq("id",id).execute()
                    else:
                        mode_Type=3
                        Counter=0
                        frameBackground[44:44 + 633, 808:808 + 414] = Modes[mode_Type]
            if mode_Type != 3:


                if 10<Counter<20:
                    mode_Type=2

                frameBackground[44:44+633,808:808+414]=Modes[mode_Type]


                if imgStudent is not None:
                    if Counter<=10:

                        # 显示学生信息
                        cv2.putText(frameBackground, str(studentInfo.data['total_attendance']), (861, 125),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                        cv2.putText(frameBackground, str(studentInfo.data['major']), (1006, 550),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(frameBackground, str(studentInfo.data['id']), (1006, 493),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(frameBackground, str(studentInfo.data['standing']), (910, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                        cv2.putText(frameBackground, str(studentInfo.data['year']), (1025, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                        cv2.putText(frameBackground, str(studentInfo.data['starting_year']), (1125, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                        (w, h), _ = cv2.getTextSize(str(studentInfo.data['name']), cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                        offset = (414 - w) // 2
                        cv2.putText(frameBackground, str(studentInfo.data['name']), (808 + offset, 445),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                        frameBackground[175:175 + 216, 909:909 + 216] = imgStudent

                Counter += 1

                if Counter>20:
                    Counter=0
                    mode_Type=0
                    studentInfo=[]
                    imgStudent=[]
                    frameBackground[44:44 + 633, 808:808 + 414] = Modes[mode_Type]



                # print("faceMatched")
                # print(studentsId[matchIndex])
                # print("matches[matchIndex]",matches[matchIndex])
    else:
        mode_Type=0
        Counter=0

    # cv2.imshow('frame',frame)
    cv2.imshow('frameBackground',frameBackground)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break