import itertools
import re

def expand_ipv6(addr):
    """将IPv6地址扩展为完整的32个半字节表示"""
    # 分割地址为两部分（可能包含::）
    parts = addr.split('::')
    
    if len(parts) == 1:
        # 没有::，地址是完整的
        groups = parts[0].split(':')
        # 扩展每个组为4个字符
        expanded = [g.zfill(4) for g in groups]
        return expanded
    else:
        # 处理有::的情况
        left, right = parts
        
        if left:
            left_groups = left.split(':')
            left_expanded = [g.zfill(4) for g in left_groups]
        else:
            left_expanded = []
            
        if right:
            right_groups = right.split(':')
            right_expanded = [g.zfill(4) for g in right_groups]
        else:
            right_expanded = []
            
        # 计算需要填充的零组数
        missing_groups = 8 - (len(left_expanded) + len(right_expanded))
        zero_groups = ['0000'] * missing_groups
        
        # 组合所有部分
        return left_expanded + zero_groups + right_expanded

def hamming_distance(addr1, addr2, check_first_groups=4):
    """计算IPv6地址前check_first_groups组的汉明距离"""
    addr1_nibbles = ''.join(expand_ipv6(addr1))
    addr2_nibbles = ''.join(expand_ipv6(addr2))
    
    # 只考虑前check_first_groups组（每组4个半字节）
    nibbles_to_check = min(len(addr1_nibbles), len(addr2_nibbles), check_first_groups * 4)
    
    distance = 0
    for i in range(nibbles_to_check):
        if addr1_nibbles[i] != addr2_nibbles[i]:
            distance += 1
    return distance

def generate_targets(seed, pattern, distance=1, check_first_groups=4):
    """生成与种子地址前check_first_groups组汉明距离为distance的目标地址，后4组可变半字节可任意替换"""
    targets = []
    seed_nibbles = ''.join(expand_ipv6(seed))
    pattern_nibbles = ''.join(expand_ipv6(pattern))
    
    # 分离前4组和后4组的可变位置
    front_var_positions = [i for i, c in enumerate(pattern_nibbles) if c == '*' and i < check_first_groups * 4]
    back_var_positions = [i for i, c in enumerate(pattern_nibbles) if c == '*' and i >= check_first_groups * 4]
    
    # 如果前4组可变位置不足，直接返回空列表
    if len(front_var_positions) < distance:
        return []
    
    # 生成前4组所有可能的distance个位置的组合
    for front_positions in itertools.combinations(front_var_positions, distance):
        # 为前4组每个位置组合生成所有可能的值组合
        for front_values in itertools.product('0123456789abcdef', repeat=distance):
            # 创建新的nibbles列表，初始化为种子值
            new_nibbles = list(seed_nibbles)
            
            # 应用前4组的变化
            valid_change = True
            for i, pos in enumerate(front_positions):
                # 确保变化后的nibble与原始不同
                if front_values[i] == seed_nibbles[pos]:
                    valid_change = False
                    break
                new_nibbles[pos] = front_values[i]
            
            # 如果前4组的变化无效，则跳过
            if not valid_change:
                continue
            
            # 生成后4组所有可能的值组合（如果有可变位置）
            if back_var_positions:
                back_value_combinations = itertools.product('0123456789abcdef', repeat=len(back_var_positions))
            else:
                back_value_combinations = [[]]  # 没有后4组可变位置时的空组合
            
            # 对后4组的每个值组合
            for back_values in back_value_combinations:
                # 复制当前的nibbles列表
                current_nibbles = new_nibbles.copy()
                
                # 应用后4组的变化
                for i, pos in enumerate(back_var_positions):
                    current_nibbles[pos] = back_values[i]
                
                # 构建新地址
                new_seed = ':'.join([''.join(current_nibbles[j:j + 4]) for j in range(0, len(current_nibbles), 4)])
                
                # 验证汉明距离（双重检查，只计算前check_first_groups组）
                if hamming_distance(seed, new_seed, check_first_groups) == distance:
                    targets.append(new_seed)
    
    return targets

def process_pattern_file(input_content, output_file_path, budget, address_count, avg_density, hamming_distance=1, check_first_groups=4):
    """处理模式文件内容并生成目标地址，同时确保去重，仅使用密度大于平均密度的模式"""
    # 初始化已生成地址集合
    generated_addresses = set()
    
    # 匹配模式、可变半字节数、密度和地址列表
    patterns = re.findall(r'Pattern: (.*?)\nVariable Nibbles: (\d+)\nDensity: (\d+\.\d+)\nAddresses:\n((?:- .*\n)*)', input_content)
    
    # 统计符合条件的模式数量
    valid_pattern_count = 0
    total_patterns = len(patterns)
    
    with open(output_file_path, 'a') as outfile:
        for pattern, var_nibbles, density_str, addresses_str in patterns:
            density = float(density_str)
            var_count = int(var_nibbles)
            
            # 计算模式在前check_first_groups组内的可变半字节数
            pattern_expanded = expand_ipv6(pattern)
            pattern_nibbles_str = ''.join(pattern_expanded)
            front_var_positions = [i for i, c in enumerate(pattern_nibbles_str) if c == '*' and i < check_first_groups * 4]
            front_var_count = len(front_var_positions)
            
            # 仅处理密度大于平均密度且前check_first_groups组内可变半字节数足够的模式
            if density > avg_density and front_var_count >= hamming_distance:
                valid_pattern_count += 1
                addresses = [addr.strip('- ').strip() for addr in addresses_str.strip().split('\n')]
                for addr in addresses:
                    targets = generate_targets(addr, pattern, hamming_distance, check_first_groups)
                    for target in targets:
                        if address_count >= budget:
                            return address_count
                        # 检查目标地址是否已经生成过
                        if target not in generated_addresses:
                            outfile.write(target + '\n')
                            generated_addresses.add(target)
                            address_count += 1
    
    print(f"模式筛选结果：{valid_pattern_count}/{total_patterns} 个模式符合要求（密度 > {avg_density:.4f} 且 前{check_first_groups}组内可变半字节数 >= {hamming_distance}）")
    return address_count