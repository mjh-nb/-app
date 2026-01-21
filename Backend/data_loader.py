# data_loader.py
import pandas as pd

# 全局变量，用于存储加载后的数据
SYMPTOM_SCHEMA = {}  # 症状定义
ID_TO_CODE_MAP = {}  # ID -> Code 映射
DISEASE_DB = {}  # 证候匹配规则库


def load_all_data(symptom_file="rules.xlsx", disease_file="diseases.xlsx", tongue_file="tongue.xlsx"):
    """
    加载 Excel 数据到全局变量中。
    请确保这三个 xlsx 文件在项目根目录下。
    """
    print("🚀 [DataLoader] 正在初始化系统数据...")

    global SYMPTOM_SCHEMA, ID_TO_CODE_MAP, DISEASE_DB

    # === 1. 加载症状定义 (rules.xlsx) ===
    try:
        df_sym = pd.read_excel(symptom_file).fillna("")
        for _, row in df_sym.iterrows():
            s_id = str(row.get('症状编码', '')).strip()
            s_code = str(row.get('症状英文', '')).strip()
            if not s_code: s_code = str(row.get('症状中文', '')).strip()

            if s_id: ID_TO_CODE_MAP[s_id] = s_code

            dims, options = [], []
            for i in range(1, 4):
                dim_name = str(row.get(f'采集维度{i}', '')).strip()
                opt_str = str(row.get(f'选项{i}', '')).strip()
                if dim_name:
                    dims.append(dim_name)
                    options.append(opt_str.split(';') if opt_str else [])

            SYMPTOM_SCHEMA[s_code] = {"dims": dims, "options": options}
        print(f"✅ [DataLoader] 加载了 {len(SYMPTOM_SCHEMA)} 个症状定义")
    except Exception as e:
        print(f"❌ [DataLoader] 加载症状表失败: {e}")

    # === 2. 加载舌象定义 (tongue.xlsx) ===
    try:
        df_tongue = pd.read_excel(tongue_file).fillna("")
        for _, row in df_tongue.iterrows():
            t_id = str(row.get('症状编码', '')).strip()
            t_code = str(row.get('英文代码', '')).strip()
            if not t_code: t_code = str(row.get('症状名称', '')).strip()
            if t_id: ID_TO_CODE_MAP[t_id] = t_code
        print(f"✅ [DataLoader] 加载了 {len(df_tongue)} 条舌象定义")
    except Exception as e:
        print(f"⚠️ [DataLoader] 舌象表加载跳过: {e}")

    # === 3. 加载证候定义 (diseases.xlsx) ===
    try:
        df_dis = pd.read_excel(disease_file).fillna("")
        for _, row in df_dis.iterrows():
            d_name = row['证候名称']
            core_raw = str(row.get('核心症状编码', '')).split(';')
            side_raw = str(row.get('非核心症状编码', '')).split(';')

            core_codes = [ID_TO_CODE_MAP.get(p.strip(), p.strip()) for p in core_raw if p.strip()]
            side_codes = [ID_TO_CODE_MAP.get(p.strip(), p.strip()) for p in side_raw if p.strip()]

            DISEASE_DB[d_name] = {"core": core_codes, "side": side_codes}
        print(f"✅ [DataLoader] 加载了 {len(DISEASE_DB)} 种证候规则")
    except Exception as e:
        print(f"❌ [DataLoader] 加载证候表失败: {e}")