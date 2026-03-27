"""
单条消息测试 - 检查保存和特征提取
"""

import asyncio
import aiohttp
import json
import time

async def single_message_test():
    user_id = "single_test_user"
    message = "你好，我是个程序员，喜欢看书"
    
    async with aiohttp.ClientSession() as session:
        print("="*70)
        print("单条消息测试")
        print("="*70)
        print(f"用户 ID: {user_id}")
        print(f"消息：{message}")
        print("="*70)
        
        payload = {
            "user_id": user_id,
            "message": message,
            "extract_features": True,
            "deep_think": False
        }
        
        print("\n发送消息...")
        try:
            async with session.post("http://localhost:8000/api/stream", json=payload) as response:
                print(f"状态码：{response.status}")
                
                full_response = ""
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if data.get('type') == 'chunk':
                            print(data.get('content', ''), end='', flush=True)
                            full_response += data.get('content', '')
                        elif data.get('type') == 'done':
                            print("\n✅ 响应完成")
                            break
                        elif data.get('type') == 'error':
                            print(f"\n❌ 错误：{data.get('content')}")
                            break
                
        except Exception as e:
            print(f"\n❌ 异常：{e}")
            import traceback
            traceback.print_exc()
        
        # 等待 5 秒让特征提取完成
        print("\n等待特征提取完成...")
        await asyncio.sleep(5)
        
        # 检查数据库
        print("\n检查数据库...")
        import sqlite3
        conn = sqlite3.connect('C:\\myProject\\MindPeek\\data\\permir.db')
        cursor = conn.cursor()
        
        # 检查对话
        cursor.execute("""
            SELECT COUNT(*) FROM conversations WHERE user_id = ?
        """, (user_id,))
        conv_count = cursor.fetchone()[0]
        print(f"  对话数量：{conv_count}")
        
        if conv_count > 0:
            cursor.execute("""
                SELECT role, content, timestamp 
                FROM conversations 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 3
            """, (user_id,))
            for conv in cursor.fetchall():
                timestamp = conv[2][:19] if conv[2] else 'N/A'
                content = conv[1][:60] if conv[1] else 'N/A'
                print(f"    [{conv[0]}] {timestamp}: {content}...")
        
        # 检查特征
        cursor.execute("""
            SELECT COUNT(*) FROM features WHERE user_id = ?
        """, (user_id,))
        feature_count = cursor.fetchone()[0]
        print(f"  特征数量：{feature_count}")
        
        if feature_count > 0:
            cursor.execute("""
                SELECT feature_type, feature_value, confidence 
                FROM features 
                WHERE user_id = ?
            """, (user_id,))
            for f in cursor.fetchall():
                print(f"    [{f[0]}] {f[1]} (置信度：{f[2]})")
        
        conn.close()
        
        print("\n" + "="*70)
        if conv_count > 0 and feature_count > 0:
            print("✅ 测试成功！对话和特征都已保存。")
        elif conv_count > 0:
            print("⚠️  对话已保存，但特征提取失败。")
        else:
            print("❌ 测试失败！对话没有被保存。")
        print("="*70)

if __name__ == "__main__":
    asyncio.run(single_message_test())
