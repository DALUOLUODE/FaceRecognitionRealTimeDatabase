
from supabase import create_client, Client

# Supabase 项目的基本信息
SUPABASE_URL = "https://lheqmfatlqoulgavjlan.supabase.co"  # 替换为你的 Project URL
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxoZXFtZmF0bHFvdWxnYXZqbGFuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MDkyMDkyNSwiZXhwIjoyMDU2NDk2OTI1fQ.jvDO0Rm-HLCyNDTVbvSfqY6ckvTB_cyr-SI8p8_vFxs"          # 替换为你的 service_role 密钥

# 初始化 Supabase 客户端
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# 测试是否连接成功（可选）
print("Supabase client initialized successfully!")

# 数据准备（模仿 Firebase 的结构）
data = {
    "1": {
        "name": "WaWa",
        "major": "computer_science",
        "year": 6,
        "last_attendance_time":"2025-01-01 00:01:25",
        "total_attendance": 8,
        "standing":"G",
        "starting_year":"2002-09-03"
    },
    "2": {
        "name": "Elon",
        "major": "AI",
        "year": 3,
        "last_attendance_time":"2025-03-03 00:01:25",
        "total_attendance": 8,
        "standing":"G",
        "starting_year":"2002-09-03"

    },
    "3": {
        "name": "Emily",
        "major": "performance",
        "year": 3,
        "last_attendance_time":"2025-02-14 00:01:25",
        "total_attendance": 8,
        "standing":"G",
        "starting_year":"2002-09-03"
    }
}

# 转换为适合表的列表格式
students_list = [{"id": key, **value} for key, value in data.items()]

# 批量插入
response = supabase.table("students").upsert(students_list).execute()
print("Inserted data:", response.data)