import numpy as np
from collections import defaultdict
from scipy.spatial import KDTree  # 新增依赖，用于计算平均间距

def load_mapped_coordinates(file_path):
    """一次性加载所有三维坐标"""
    ipv6_addrs = []
    coordinates = []
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            ipv6_addrs.append(parts[0])
            coords = list(map(float, parts[1:4]))  # 提取三维坐标
            coordinates.append(coords)
    return ipv6_addrs, np.array(coordinates)


    
#     return point_labels
def calculate_harmonic_mean_spacing(coordinates, min_value=1e-10):
    """计算调和平均最近邻距离"""
    if len(coordinates) < 2:
        return min_value
    
    tree = KDTree(coordinates)
    distances = tree.query(coordinates, k=2)[0][:, 1]  # 获取每个点的次近邻距离
    
    # 过滤零值（防止除以零），并确保所有距离不小于最小值
    valid_distances = np.maximum(distances, min_value)
    
    # 计算调和平均数：n / (1/x1 + 1/x2 + ... + 1/xn)
    harmonic_mean = len(valid_distances) / np.sum(1.0 / valid_distances)
    
    return harmonic_mean

def grid_clustering(coordinates, d=None, min_cluster_size=10):
    """基于调和平均和26邻域的网格聚类算法"""
    if d is None:
        harmonic_mean = calculate_harmonic_mean_spacing(coordinates)
        d = 1.0 * harmonic_mean  # 网格尺寸取调和平均数的2倍
        #print(f"调和平均最近邻距离：{harmonic_mean:.20f}")
        print(f"使用网格尺寸 d = {d:.20f}")
    
    # 空间网格化（使用64位整数防止坐标溢出）
    grid_coords = np.floor(coordinates / d).astype(np.int64)
    
    # 构建网格到点的映射
    grid_points = defaultdict(list)
    for idx, (x, y, z) in enumerate(grid_coords):
        grid_points[(x, y, z)].append(idx)
    
    # 26邻域定义（包含X轴偏移）
    neighbors = [
        (dx, dy, dz)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        for dz in (-1, 0, 1)
        if not (dx == 0 and dy == 0 and dz == 0)
    ]
    
    # 哈希映射聚类
    cluster_labels = {}
    current_label = 0
    
    for grid in grid_points.keys():
        # 检查所有26个邻域网格
        neighbor_labels = set()
        for nb in neighbors:
            nb_grid = (grid[0] + nb[0], grid[1] + nb[1], grid[2] + nb[2])
            if nb_grid in cluster_labels:
                neighbor_labels.add(cluster_labels[nb_grid])
        
        # 继承最小标签或分配新标签
        if neighbor_labels:
            cluster_labels[grid] = min(neighbor_labels)
        else:
            cluster_labels[grid] = current_label
            current_label += 1
    
    # 识别孤立网格（无任何邻域点的网格）
    isolated_grids = set()
    for grid in grid_points.keys():
        has_neighbor = any(
            (grid[0] + nb[0], grid[1] + nb[1], grid[2] + nb[2]) in grid_points
            for nb in neighbors
        )
        if not has_neighbor:
            isolated_grids.add(grid)
    
    # 点归属与噪声处理
    point_labels = np.full(len(coordinates), -1, dtype=int)
    for grid, label in cluster_labels.items():
        point_labels[grid_points[grid]] = label if grid not in isolated_grids else -1
    
    # 过滤小簇
    cluster_size = defaultdict(int)
    for lbl in point_labels:
        if lbl != -1:
            cluster_size[lbl] += 1
    
    for idx in range(len(point_labels)):
        if cluster_size[point_labels[idx]] < min_cluster_size:
            point_labels[idx] = -1
    
    return point_labels
