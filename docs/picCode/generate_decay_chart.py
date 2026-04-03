"""
生成特征衰减函数图表
"""
import numpy as np
import matplotlib.pyplot as plt
import os

# 衰减函数参数
stability_period = 30  # 稳定期（天）
decay_rate = 0.05      # 衰减率
min_confidence = 0.3   # 最小置信度
initial_confidence = 0.9  # 初始置信度

# 时间范围
max_days = 180  # 6个月
t = np.arange(0, max_days + 1, 1)

# 计算置信度
confidence = []
for day in t:
    if day <= stability_period:
        # 稳定期：置信度保持不变
        conf = initial_confidence
    else:
        # 衰减期：使用对数衰减函数
        delta_t = day - stability_period
        conf = initial_confidence - 0.3 * (initial_confidence - min_confidence) * np.log(1 + delta_t * decay_rate)
        # 确保不低于最小置信度
        conf = max(conf, min_confidence)
    confidence.append(conf)

# 创建图表
plt.figure(figsize=(10, 6))

# 绘制衰减曲线
plt.plot(t, confidence, 'b-', linewidth=2, label='置信度')

# 绘制稳定期区域
plt.axvspan(0, stability_period, alpha=0.1, color='green', label='稳定期')

# 绘制最小阈值线
plt.axhline(y=min_confidence, color='r', linestyle='--', linewidth=1, label=f'最小阈值 ({min_confidence})')

# 绘制稳定期结束线
plt.axvline(x=stability_period, color='gray', linestyle='--', linewidth=1, label=f'稳定期结束 ({stability_period}天)')

# 设置标题和标签
plt.title('特征置信度衰减函数', fontsize=14, fontweight='bold')
plt.xlabel('时间（天）', fontsize=12)
plt.ylabel('置信度', fontsize=12)

# 设置坐标轴范围
plt.xlim(0, max_days)
plt.ylim(0, 1)

# 添加网格
plt.grid(True, linestyle='--', alpha=0.7)

# 添加图例
plt.legend()

# 保存图表
output_dir = 'docs/images'
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'decay_function_cn.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"图表已保存到: {output_path}")

# 生成英文版本
plt.figure(figsize=(10, 6))
plt.plot(t, confidence, 'b-', linewidth=2, label='Confidence')
plt.axvspan(0, stability_period, alpha=0.1, color='green', label='Stability Period')
plt.axhline(y=min_confidence, color='r', linestyle='--', linewidth=1, label=f'Min Threshold ({min_confidence})')
plt.axvline(x=stability_period, color='gray', linestyle='--', linewidth=1, label=f'Stability End ({stability_period} days)')
plt.title('Feature Confidence Decay Function', fontsize=14, fontweight='bold')
plt.xlabel('Time (days)', fontsize=12)
plt.ylabel('Confidence', fontsize=12)
plt.xlim(0, max_days)
plt.ylim(0, 1)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()

output_path_en = os.path.join(output_dir, 'decay_function_en.png')
plt.savefig(output_path_en, dpi=300, bbox_inches='tight')
plt.close()

print(f"英文图表已保存到: {output_path_en}")

# 生成日文版本
plt.figure(figsize=(10, 6))
plt.plot(t, confidence, 'b-', linewidth=2, label='信頼度')
plt.axvspan(0, stability_period, alpha=0.1, color='green', label='安定期間')
plt.axhline(y=min_confidence, color='r', linestyle='--', linewidth=1, label=f'最小閾値 ({min_confidence})')
plt.axvline(x=stability_period, color='gray', linestyle='--', linewidth=1, label=f'安定期間終了 ({stability_period}日)')
plt.title('特徴信頼度減衰関数', fontsize=14, fontweight='bold')
plt.xlabel('時間（日）', fontsize=12)
plt.ylabel('信頼度', fontsize=12)
plt.xlim(0, max_days)
plt.ylim(0, 1)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()

output_path_ja = os.path.join(output_dir, 'decay_function_ja.png')
plt.savefig(output_path_ja, dpi=300, bbox_inches='tight')
plt.close()

print(f"日文图表已保存到: {output_path_ja}")
print("\n图表生成完成！")
