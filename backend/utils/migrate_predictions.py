"""
数据库迁移脚本：添加 user_predictions 表
"""
import sqlite3
from datetime import datetime
from backend.core.config import config_manager

DB_PATH = config_manager.get_database_path()

def migrate():
    """执行数据库迁移"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建 user_predictions 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                prediction TEXT NOT NULL,
                category TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                reasoning TEXT,
                timeframe TEXT,
                observable_signals JSON DEFAULT '[]',
                is_verified BOOLEAN DEFAULT 0,
                verified_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_user_id 
            ON user_predictions(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_category 
            ON user_predictions(category)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_created_at 
            ON user_predictions(created_at)
        """)
        
        conn.commit()
        print("Success: user_predictions table created")
        
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
