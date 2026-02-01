# data_loader.py
import pandas as pd
import os

# 全局缓存，用于存储加载完成的诊断规则表
# Key: 辨证类型 (如'八纲'), Value: DataFrame
DIAGNOSIS_TABLES = {}


def load_all_data():
    """
    初始化诊断规则库，批量读取Excel配置文件
    """
    print("🚀 [DataLoader] 正在初始化诊断数据库...")
    global DIAGNOSIS_TABLES

    # 规则文件存放目录
    BASE_DIR = "中医诊断学"

    # 逻辑Key与物理文件名的映射配置
    file_mapping = {
        '八纲': '八纲证候判断表.xlsx',
        '病因': '病因辨证表.xlsx',
        '六经': '六经辨证表.xlsx',
        '卫气营血': '卫气营血表.xlsx',  # 需核对实际文件名是否包含“辨证”二字
        '气血津液': '气血津液辨证表.xlsx',
        '脏腑': '脏腑辨证表.xlsx',
    }

    loaded_count = 0

    for key, filename in file_mapping.items():
        # 构建完整文件路径
        full_path = os.path.join(BASE_DIR, filename)

        if os.path.exists(full_path):
            try:
                # 加载数据
                df = pd.read_excel(full_path)

                # 去除列名可能存在的空白字符
                df.columns = df.columns.str.strip()

                # 处理NaN空值
                df = df.fillna("")

                # 写入全局缓存
                DIAGNOSIS_TABLES[key] = df
                print(f"✅ [DataLoader] 加载成功: {full_path} ({len(df)} 行)")
                loaded_count += 1
            except Exception as e:
                print(f"❌ [DataLoader] 读取文件出错 [{full_path}]: {e}")
        else:
            # 容错处理：如果指定目录未找到，尝试回退到根目录查找
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