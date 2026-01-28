import os

# 1. 认知映射表保持不变
FOLDER_COMMENTS = {
    "src": "核心代码库：所有 核心代码逻辑 的集合",
    "src/vision": "视觉模块：负责液滴识别、轨迹追踪",
    "src/control": "控制逻辑:PID 计算与指令生成",
    "src/_old_code": "历史代码：存放旧版本代码以备查阅",
    "drivers": "硬件驱动库：屏蔽底层通讯细节",
    "drivers/arduino": "下位机:Arduino 固件源码",
    "drivers/raw_setup": "环境依赖:存放本地(由硬件自带的)驱动, Git 暂不追踪",
    "data": "实验数据区：存放 .mp4 和原始记录",
    "docs": "文档区：包含接线图与参考文献",
}

def get_ignored_rules():
    """点火前仅执行一次：提取过滤规则"""
    ignored = {".git", "__pycache__", "venv", "Logic_tree.txt"} # 增加对输出文件自身的忽略
    if os.path.exists(".gitignore"):
        with open(".gitignore", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    ignored.add(line.rstrip("/"))
    return ignored

def generate_tree(path, file_obj, ignored_rules, base_path, prefix=""):
    try:
        # 过滤掉隐藏文件和噪音文件
        files = [f for f in os.listdir(path) if f not in ignored_rules]
    except PermissionError:
        return

    for i, file in enumerate(sorted(files)):
        full_path = os.path.join(path, file)
        # 统一使用斜杠，适配跨平台
        rel_path = os.path.relpath(full_path, base_path).replace("\\", "/")
        
        # 判定是否命中通配符（如 .mp4）
        if any(file.endswith(rule.replace("*", "")) for rule in ignored_rules if "*" in rule):
            continue

        is_last = (i == len(files) - 1)
        connector = "└── " if is_last else "├── "
        
        comment = FOLDER_COMMENTS.get(rel_path, "")
        line = f"{prefix}{connector}{file}{'  # ' + comment if comment else ''}"
        
        print(line)
        file_obj.write(line + "\n")
        
        if os.path.isdir(full_path):
            new_prefix = prefix + ("    " if is_last else "│   ")
            generate_tree(full_path, file_obj, ignored_rules, base_path, new_prefix)

# --- 点火程序 ---
start_base = os.path.dirname(os.path.abspath(__file__)) 
output_file = os.path.join(start_base, "Logic_tree.txt")
rules = get_ignored_rules()

print(f"--- 正在生成文件夹架构树 [Refined Edition] ---")
with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"Project: {os.path.basename(start_base)}\n" + "="*40 + "\n")
    generate_tree(start_base, f, rules, start_base)

print(f"--- 导出完成！(已略去缓存以及实验数据等**非代码核心内容**) ---")
input("\n 按回车键退出...") # 类似于 getchar()