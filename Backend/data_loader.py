# data_loader.py
import pandas as pd
import os

# === 全局变量 ===
# 只存储诊断用的表格数据
# 结构: { '八纲': DataFrame, '脏腑': DataFrame, ... }
DIAGNOSIS_TABLES = {} 

def load_all_data():
    """
    只加载用于决策树诊断的 Excel 表格
    """
    print("🚀 [DataLoader] 正在初始化诊断数据库...")
    global DIAGNOSIS_TABLES
    
    # 映射关系：代码逻辑Key -> 实际文件名
    file_mapping = {
        '八纲': '中医诊断学/八纲证候判断表.xlsx',
        '病因': '中医诊断学/病因辨证表.xlsx',
        '六经': '中医诊断学/六经辨证表.xlsx',
        '卫气营血': '中医诊断学/卫气营血表.xlsx',
        '气血津液': '中医诊断学/气血津液辨证表.xlsx',
        '脏腑': '中医诊断学/脏腑辨证表.xlsx',
    }

    for key, filename in file_mapping.items():
        if os.path.exists(filename):
            try:
                # 读取 Excel
                df = pd.read_excel(filename)
                
                # 清洗列名 (防止空格干扰)
                df.columns = df.columns.str.strip()
                
                # 填充空值
                df = df.fillna("")
                
                # 存入全局字典
                DIAGNOSIS_TABLES[key] = df
                print(f"✅ [DataLoader] 已加载表格 [{key}]: {len(df)} 条规则")
            except Exception as e:
                print(f"❌ [DataLoader] 加载表格失败 [{filename}]: {e}")
        else:
            print(f"❌ [DataLoader] 文件缺失: {filename}")

def get_table(key):
    return DIAGNOSIS_TABLES.get(key, pd.DataFrame())