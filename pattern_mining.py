from collections import defaultdict
from mapping import expand_ipv6 
import numpy as np

# 定义三维轴对应的半字节范围
X_AXIS_NIBBLES = slice(0, 12)   # 前3组（48位）
Y_AXIS_NIBBLES = slice(12, 16)  # 第4组（16位）
Z_AXIS_NIBBLES = slice(16, 32)  # 后4组（64位）

def ipv6_to_nibbles(ipv6_address: str) -> list:
    """将IPv6地址转换为32个半字节列表"""
    full_groups = expand_ipv6(ipv6_address)
    return [c for group in full_groups for c in group.lower()]

def cluster_pattern_mining(cluster_content, pattern_file=None):
    """挖掘聚类模式并生成可视化"""
    # 加载聚类数据
    cluster_data = defaultdict(list)
    lines = cluster_content.split('\n')
    for line in lines[1:]:  # 跳过表头
        if line:
            addr, cluster_id = line.strip().split(',')
            cluster_id = int(cluster_id)
            # 排除类标签为 -1 的噪声点
            if cluster_id != -1:
                cluster_data[cluster_id].append(addr)
    
    # 分析每个聚类
    pattern_results = []
    axis_var_counts = defaultdict(lambda: defaultdict(int))  # 轴->可变半字节数->聚类数
    
    for cluster_id, addrs in cluster_data.items():
        if not addrs:
            continue
            
        # 生成聚类模式
        nibble_matrix = [ipv6_to_nibbles(addr) for addr in addrs]
        pattern = [''] * 32
        
        for axis, axis_slice in [('X', X_AXIS_NIBBLES), ('Y', Y_AXIS_NIBBLES), ('Z', Z_AXIS_NIBBLES)]:
            for col in range(axis_slice.start, axis_slice.stop):
                column_values = [row[col] for row in nibble_matrix]
                pattern[col] = column_values[0] if all(v == column_values[0] for v in column_values) else '*'
        
        # 计算各轴可变半字节数
        x_var = pattern[X_AXIS_NIBBLES].count('*')
        y_var = pattern[Y_AXIS_NIBBLES].count('*')
        z_var = pattern[Z_AXIS_NIBBLES].count('*')
        total_var = x_var + y_var + z_var
        
        # 更新统计
        axis_var_counts['X'][x_var] += 1
        axis_var_counts['Y'][y_var] += 1
        axis_var_counts['Z'][z_var] += 1
        
        # 生成模式字符串
        pattern_str = ':'.join([''.join(pattern[i*4:(i+1)*4]) for i in range(8)])
        
        # 修改密度计算：地址数除以16的可变半字节次方
        # density = len(addrs) * 32 / (130000 * total_var) if total_var > 0 else float('inf')
        density = len(addrs) / total_var if total_var > 0 else float('inf')
        pattern_results.append((cluster_id, pattern_str, total_var, density, len(addrs), addrs))
    
    # 按密度排序
    pattern_results.sort(key=lambda x: x[3], reverse=True)
    
    # 生成模式文件内容
    pattern_content = ""
    for res in pattern_results:
        pattern_content += f"Pattern: {res[1]}\n"
        pattern_content += f"Variable Nibbles: {res[2]}\n"
        pattern_content += f"Density: {res[3]:.15f}\n"  # 增加密度显示精度
        pattern_content += "Addresses:\n"
        for addr in res[5]:
            pattern_content += f"- {addr}\n"
        pattern_content += "\n"  # 模式间空行分隔
    
    if pattern_file:
        with open(pattern_file, 'w') as f:
            f.write(pattern_content)
    
    # 返回平均密度
    avg_density = sum(res[3] for res in pattern_results if res[3] != float('inf')) / len(pattern_results)
    return pattern_content, avg_density