"""直接测试同步特征提取函数"""
import sys
sys.path.insert(0, 'C:\\myProject\\MindPeek')

from backend.utils.sync_feature_extractor import extract_features_sync

print("测试同步特征提取函数...")
result = extract_features_sync(
    "test_user_sync", 
    "你好，我叫小明，是个程序员", 
    "你好！很高兴见到你，有什么我可以帮助你的吗？"
)
print(f"\n结果：{result}")
