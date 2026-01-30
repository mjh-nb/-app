# data_loader.py
import pandas as pd
import os

# === 全局变量 ===
# 存储加载后的 DataFrame
# 结构: { '八纲': DataFrame, '脏腑': DataFrame, ... }
DIAGNOSIS_TABLES = {} 

def load_all_data():
    """
    加载用于决策树诊断的 Excel 表格
    """
    print("🚀 [DataLoader] 正在初始化诊断数据库...")
    global DIAGNOSIS_TABLES
    
    # ⬇️⬇️⬇️ 修改点：指定文件夹名称 ⬇️⬇️⬇️
    BASE_DIR = "中医诊断学" 
    
    # 映射关系：代码逻辑Key -> 实际文件名
    # 请确保你的文件名和这里完全一致（包括后缀）
    file_mapping = {
        '八纲': '八纲证候判断表.xlsx',
        '病因': '病因辨证表.xlsx',
        '六经': '六经辨证表.xlsx',
        '卫气营血': '卫气营血表.xlsx', # 注意：有的文件可能叫 '卫气营血辨证表.xlsx'，请核对你的实际文件名！
        '气血津液': '气血津液辨证表.xlsx',
        '脏腑': '脏腑辨证表.xlsx',
    }

    loaded_count = 0

    for key, filename in file_mapping.items():
        # 拼接完整路径: 中医诊断学/八纲证候判断表.xlsx
        full_path = os.path.join(BASE_DIR, filename)
        
        if os.path.exists(full_path):
            try:
                # 读取 Excel
                df = pd.read_excel(full_path)
                
                # 清洗列名 (防止空格干扰)
                df.columns = df.columns.str.strip()
                
                # 填充空值
                df = df.fillna("")
                
                # 存入全局字典
                DIAGNOSIS_TABLES[key] = df
                print(f"✅ [DataLoader] 加载成功: {full_path} ({len(df)} 行)")
                loaded_count += 1
            except Exception as e:
                print(f"❌ [DataLoader] 读取文件出错 [{full_path}]: {e}")
        else:
            # 尝试在根目录找一下，防止为了兼容性
            if os.path.exists(filename):
                print(f"⚠️ [DataLoader] 在根目录找到了 {filename} (建议移动到 '{BASE_DIR}' 文件夹)")
                try:
                    df = pd.read_excel(filename).fillna("")
                    df.columns = df.columns.str.strip()
                    DIAGNOSIS_TABLES[key] = df
                    loaded_count += 1
                except:
                    pass
            else:
                print(f"❌ [DataLoader] 文件缺失: {full_path}")

    if loaded_count == 0:
        print("🛑 [DataLoader] 警告：没有加载到任何表格！请检查文件夹名和文件名是否正确！")

def get_table(key):
    return DIAGNOSIS_TABLES.get(key, pd.DataFrame())