# db_config.py
import os
import pymysql
from dotenv import load_dotenv

# 使 python-dotenv 读取 .env 文件
load_dotenv()

# 从环境变量读取,即.env文件中
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "aeroguard")

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor  # 返回字典格式的查询结果
    )
