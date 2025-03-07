
from supabase import create_client, Client

# 常量定义
SUPABASE_URL = "dududu.supabase.co"  # Supabase 项目 URL
SUPABASE_SERVICE_KEY = "dududududu"          # 替换为你的 service_role 密钥
TABLE_NAME = "students"  # 目标表名

# 初始化 Supabase 客户端
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
print("Supabase client initialized successfully!")

def prepare_student_data() -> list:
    """准备学生数据，将字典格式转换为适合 Supabase 表的列表格式"""
    data = {
        "1": {
            "name": "WaWa",
            "major": "computer_science",
            "year": 6,
            "last_attendance_time": "2025-01-01 00:01:25",
            "total_attendance": 8,
            "standing": "G",
            "starting_year": "2002"
        },
        "2": {
            "name": "Elon",
            "major": "AI",
            "year": 3,
            "last_attendance_time": "2025-03-03 00:01:25",
            "total_attendance": 8,
            "standing": "G",
            "starting_year": "2003"
        },
        "3": {
            "name": "Emily",
            "major": "performance",
            "year": 3,
            "last_attendance_time": "2025-02-14 00:01:25",
            "total_attendance": 8,
            "standing": "G",
            "starting_year": "2006"
        }
    }
    return [{"id": key, **value} for key, value in data.items()]

def insert_data_to_supabase(data: list) -> None:
    """将学生数据批量插入到 Supabase 数据库"""
    try:
        response = supabase.table(TABLE_NAME).upsert(data).execute()
        print("Inserted data:", response.data)
    except Exception as e:
        print(f"Failed to insert data: {str(e)}")

def main():
    """主函数：准备数据并插入到 Supabase"""
    student_data = prepare_student_data()
    insert_data_to_supabase(student_data)

if __name__ == "__main__":
    main()