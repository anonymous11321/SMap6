import os
import time
import logging
import subprocess
from mapping import *
from clustering import *
from pattern_mining import *
from target_generation import *
from config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='smap6.log'
)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def main():
    logging.info("开始运行 SMap6 程序")
    total_start_time = time.time()
    
    # 从配置文件读取参数
    budget = Config.BUDGET
    input_file = Config.INPUT_FILE
    output_target = Config.OUTPUT_TARGET
    output_zmap = Config.OUTPUT_ZMAP
    source_ip = Config.SOURCE_IP
    rate = Config.SCAN_RATE

    # 创建输出目录
    os.makedirs("Data", exist_ok=True)
    logging.info("已创建/验证Data目录")

    # 初始化目标文件（如果存在则删除）
    if os.path.exists(output_target):
        os.remove(output_target)
        logging.info(f"已删除现有目标文件: {output_target}")

    # 1. 地址映射
    logging.info("开始处理IPv6地址映射")
    ipv6_addrs = []
    with open(input_file, 'r') as f:
        ipv6_addrs = [line.strip() for line in f]
    logging.info(f"成功加载{len(ipv6_addrs)}个IPv6地址")

    coordinates = []
    for ipv6_addr in ipv6_addrs:
        try:
            x, y, z = process_addresses(ipv6_addr)
            coordinates.append([x, y, z])
        except ValueError as ve:
            logging.warning(f"处理地址{ipv6_addr}失败: {ve}")
    coordinates = np.array(coordinates)
    logging.info(f"完成地址映射，共生成{len(coordinates)}个三维坐标")

    # 2. 聚类处理
    logging.info("开始执行网格聚类算法")
    min_cluster_size = 10  # 可在config中配置
    labels = grid_clustering(coordinates, min_cluster_size=min_cluster_size)
    logging.info("聚类处理完成")

    # 3. 模式挖掘与分析
    logging.info("开始挖掘聚类模式")
    # 生成内存中的聚类内容（不写入文件）
    cluster_lines = ["address,cluster_id"]
    for addr, label in zip(ipv6_addrs, labels):
        cluster_lines.append(f"{addr},{label}")
    cluster_content = "\n".join(cluster_lines)
    
    # 调用模式挖掘（返回模式内容和平均密度）
    pattern_content, avg_density = cluster_pattern_mining(cluster_content)
    logging.info(f"模式挖掘完成，平均密度: {avg_density:.4f}")

    # 4. 生成目标地址
    logging.info("开始生成目标地址...")
    generated_count = process_pattern_file(
        pattern_content,
        output_target,
        budget=budget,
        address_count=0,
        avg_density=avg_density
    )
    logging.info(f"成功生成{generated_count}个目标地址（预算={budget}）")

    # 5. 调用zmap进行扫描（仅终端显示，不写入日志）
    logging.info("开始调用zmap进行扫描...")  # 仅记录扫描开始
    zmap_command = f"zmap --ipv6-target-file {output_target} -o {output_zmap} --ipv6-source-ip={source_ip} -r {rate} -M icmp6_echoscan"
    
    try:
        # 使用 Popen 执行命令并实时获取输出
        process = subprocess.Popen(
            zmap_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 将 stderr 重定向到 stdout
            universal_newlines=True,
            bufsize=1
        )
        
        # 实时显示 zmap 输出（不写入日志）
        print("\n===== zmap 扫描进度 =====")
        for line in iter(process.stdout.readline, ''):
            print(line, end='')  # 仅在终端显示，不记录到日志
        
        # 等待进程完成并获取返回码
        return_code = process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, zmap_command)
            
        print("===== zmap 扫描完成 =====")
        logging.info("zmap 扫描成功完成")  # 仅记录扫描成功状态
        
    except subprocess.CalledProcessError as e:
        logging.error(f"zmap 扫描失败，返回码: {e.returncode}")  # 仅记录错误状态，不包含具体输出
        print(f"\nzmap 扫描失败，返回码: {e.returncode}")

    total_time = time.time() - total_start_time
    logging.info(f"所有操作完成，总耗时: {total_time:.2f}秒")
    print(f"\n完成所有操作，总耗时: {total_time:.2f} 秒")
    print("结果已保存至相应目录")

if __name__ == "__main__":
    main()