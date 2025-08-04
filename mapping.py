import os

def expand_ipv6(ipv6_address: str) -> list:
    """
    按照用户指定逻辑展开IPv6地址为8组16位格式
    处理::零压缩，确保每组4位十六进制
    """
    ipv6_address = ipv6_address.lower()  # 转换为小写

    if '::' in ipv6_address:
        left, right = ipv6_address.split('::', 1)  # 最多一个零压缩点
        left_parts = left.split(':') if left else []
        right_parts = right.split(':') if right else []
        total_parts = len(left_parts) + len(right_parts)
        missing_parts = 8 - total_parts
        full_parts = left_parts + ['0000'] * missing_parts + right_parts
    else:
        full_parts = ipv6_address.split(':')

    # 补全每组为4位，处理空字符串（如末尾或开头的::导致的空组）
    full_parts = [part.zfill(4) for part in full_parts if part != '']  # 过滤空字符串（处理异常输入）
    # 确保正好8组（处理非法输入，如超过8组的情况）
    if len(full_parts) > 8:
        full_parts = full_parts[:8]  # 截断到前8组
    while len(full_parts) < 8:
        full_parts.append('0000')  # 补全到8组

    return full_parts

def ipv6_to_3d_coordinates(ipv6_str: str):
    """
    将IPv6地址映射到三维空间 (X, Y, Z)
    X轴：前48位（3组×16位）
    Y轴：中间16位（第4组）
    Z轴：后64位（4组×16位）
    返回值：(X_normalized, Y_normalized, Z_normalized)
    """
    try:
        # 1. 地址补全与分组
        groups = expand_ipv6(ipv6_str)
        if len(groups) != 8:
            raise ValueError("Invalid IPv6 address format")

        # 2. 转换为整数（每组16位）
        group_ints = [int(g, 16) for g in groups]

        # 3. 计算各维度原始值
        # X轴：前3组（48位，3×16）
        x = (group_ints[0] << 32) | (group_ints[1] << 16) | group_ints[2]
        # Y轴：第4组（16位）
        y = group_ints[3]
        # Z轴：后4组（64位，4×16）
        z = (group_ints[4] << 48) | (group_ints[5] << 32) | (group_ints[6] << 16) | group_ints[7]

        # 4. 归一化（映射到[0, 1)，保留更高精度）
        x_normalized = x / (2 ** 48)
        y_normalized = y / (2 ** 16)
        z_normalized = z / (2 ** 64)

        return (x_normalized, y_normalized, z_normalized)

    except Exception as e:
        raise ValueError(f"Failed to parse IPv6 address: {e}")

def process_addresses(ipv6_address):
    """
    对单个IPv6地址进行三维空间映射
    """
    try:
        x, y, z = ipv6_to_3d_coordinates(ipv6_address)
        return x, y, z
    except ValueError as ve:
        print(f"Error processing address {ipv6_address}: {ve}")