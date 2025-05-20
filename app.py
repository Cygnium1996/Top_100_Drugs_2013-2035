# app.py
# 运行前安装依赖：
# pip install streamlit pandas openpyxl

import streamlit as st
import pandas as pd
import colorsys
from pandas.api.types import is_scalar

st.title('药物时间序列表格高亮')

@st.cache_data
def load_data():
    # 读取时间序列表（第一个 sheet），第一行为年份
    df_ts = pd.read_excel('工作簿1.xlsx', sheet_name=0, header=0)
    # 读取详细信息表（第二个 sheet）并重命名列
    df_detail = pd.read_excel('工作簿1.xlsx', sheet_name=1, header=0)
    df_detail = df_detail.rename(columns={
        df_detail.columns[2]: 'Drug',
        df_detail.columns[3]: 'Target',
        df_detail.columns[5]: 'Therapeutic Area'
    })
    # 构建药物到领域和靶点的映射
    area_map = df_detail.set_index('Drug')['Therapeutic Area'].to_dict()
    target_map = df_detail.set_index('Drug')['Target'].to_dict()
    return df_ts, area_map, target_map

# 加载数据
df_ts, drug_area, drug_target = load_data()

# 获取所有治疗领域列表
areas = sorted({area for area in drug_area.values() if pd.notna(area)})

# 从 HSL 转换到 Hex 的函数
def gen_hex_color(index, total):
    h = index / total
    l = 0.8
    s = 0.7
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return '#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255))

# 默认颜色映射（Hex）
default_color_map = {area: gen_hex_color(i, len(areas)) for i, area in enumerate(areas)}

# 侧边栏：选择治疗领域
selected_areas = st.sidebar.multiselect('选择治疗领域', areas)

# 根据已选领域，获取对应靶点列表
available_targets = []
if selected_areas:
    available_targets = sorted({
        drug_target[drug] for drug in drug_target
        if drug_area.get(drug) in selected_areas and pd.notna(drug_target[drug])
    })

# 侧边栏：二级多选靶点（默认全选已选领域下所有靶点）
selected_targets = st.sidebar.multiselect(
    '选择靶点',
    available_targets,
    default=available_targets
)

# 侧边栏：自定义颜色（Hex）
st.sidebar.markdown('### 自定义颜色（按领域）')
custom_color_map = {}
for area in areas:
    custom_color_map[area] = st.sidebar.color_picker(
        label=area,
        value=default_color_map[area],
        key=f'color_{area}'
    )

# 单元格着色函数（双重过滤：领域 + 靶点）
def color_cell(val):
    if not is_scalar(val) or pd.isna(val):
        return ''
    area = drug_area.get(val)
    target = drug_target.get(val)
    if area in selected_areas and target in selected_targets:
        return f'background-color: {custom_color_map.get(area, default_color_map.get(area))}'
    return ''

# 应用样式并展示
styled = df_ts.style.map(color_cell)
st.dataframe(styled, use_container_width=True)

# 运行程序：
# 在终端中执行：streamlit run app.py