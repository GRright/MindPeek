"""
数据库迁移脚本：添加 feature_count_at_generation 字段到 user_predictions 表
"""
import sqlite3

DB_PATH = 'C:\\myProject\\MindPeek\\data\\permir.db'

def migrate():
    """执行数据库迁移"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 添加 feature_count_at_generation 字段
        cursor.execute("""
            ALTER TABLE user_predictions
            ADD COLUMN feature_count_at_generation INTEGER DEFAULT 0
        """)
        
        conn.commit()
        print("Success: feature_count_at_generation column added")
        
        # 验证表结构
        cursor.execute("PRAGMA table_info(user_predictions)")
        columns = cursor.fetchall()
        print("Table columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting database migration...")
    migrate()
