"""
社交电商运营分析看板
功能：固定使用 data/active_data.csv，RFM动态分层、Lift偏离度分析、转化链路、策略矩阵下钻
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ==================== 配置与初始化 ====================
st.set_page_config(
    page_title="社交电商运营分析看板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ==================== session_state 初始化 ====================
if 'f_threshold' not in st.session_state:
    st.session_state.f_threshold = 20
if 'm_threshold' not in st.session_state:
    st.session_state.m_threshold = 0.0
if 'funnel_active_steps' not in st.session_state:
    st.session_state.funnel_active_steps = {
        '1. 浏览', '2. 互动', '3. 加购', '4. 领券', '5. 用券', '6. 购买'
    }

# ==================== 辅助函数 ====================
def safe_rate(numerator, denominator):
    """安全计算比率，分母为0时返回0"""
    return numerator / denominator if denominator > 0 else 0

def assign_bin_order(df, bin_col, order_list):
    """将分箱列转为有序分类，确保图表按指定顺序排列"""
    df[bin_col] = pd.Categorical(df[bin_col], categories=order_list, ordered=True)
    return df

# ==================== 数据生成函数 ====================
@st.cache_data(show_spinner=False)
def generate_mock_data(n_samples=100, random_seed=42):
    """生成符合社交电商分布的伪数据"""
    np.random.seed(random_seed)
    categories = ['服饰鞋包', '美妆护肤', '食品饮料', '家居用品', '电子产品', '图书文娱', '运动户外']

    data = {
        'user_id': np.arange(1, n_samples + 1),
        'item_id': np.random.randint(1, 500, n_samples),
        'age': np.random.normal(27, 5, n_samples).round(0).astype(int).clip(18, 60),
        'gender': np.random.choice([0, 1], n_samples, p=[0.6, 0.4]),
        'user_level': np.random.randint(1, 8, n_samples),
        'purchase_freq': np.random.poisson(18, n_samples),
        'total_spend': np.random.lognormal(6, 0.8, n_samples).round(2),
        'register_days': np.random.randint(1, 1000, n_samples),
        'follow_num': np.random.poisson(50, n_samples),
        'fans_num': np.random.poisson(100, n_samples),
        'price': np.random.lognormal(4, 0.6, n_samples).round(2),
        'discount_rate': np.random.uniform(0, 0.6, n_samples).round(2),
        'category': np.random.choice(categories, n_samples),
        'title_length': np.random.randint(5, 50, n_samples),
        'title_emo_score': np.random.uniform(0.3, 0.9, n_samples).round(2),
        'img_count': np.random.randint(1, 10, n_samples),
        'has_video': np.random.choice([0, 1], n_samples, p=[0.3, 0.7]),
        'like_num': np.random.poisson(50, n_samples),
        'comment_num': np.random.poisson(8, n_samples),
        'share_num': np.random.poisson(3, n_samples),
        'collect_num': np.random.poisson(5, n_samples),
        'is_follow_author': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        'add2cart': np.random.choice([0, 1], n_samples, p=[0.6, 0.4]),
        'coupon_received': np.random.choice([0, 1], n_samples, p=[0.45, 0.55]),
        'coupon_used': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        'pv_count': np.random.poisson(8, n_samples),
        'last_click_gap': np.random.uniform(0, 96, n_samples).round(1),
        'interaction_rate': np.random.uniform(0.01, 0.5, n_samples).round(4),
        'purchase_intent': np.random.uniform(0.1, 0.9, n_samples).round(2),
        'freshness_score': np.random.uniform(0.2, 1.0, n_samples).round(2),
        'social_influence': np.random.uniform(0.1, 0.95, n_samples).round(2),
        'label': np.random.choice([0, 1], n_samples, p=[0.8, 0.2])
    }
    return pd.DataFrame(data)

# ==================== 数据加载函数（带缓存） ====================
@st.cache_data(show_spinner="正在加载数据...")
def load_data():
    """固定加载 data/active_data.csv，不存在则自动生成兜底数据"""
    file_path = os.path.join(DATA_DIR, "active_data.csv")
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception:
            pass

    # 兜底：生成 Mock 数据并保存为 active_data.csv
    df = generate_mock_data(100)
    df.to_csv(file_path, index=False)
    return df

# ==================== RFM 分层计算 ====================
def compute_rfm(df, f_threshold, m_threshold):
    """基于F和M阈值进行四象限分层"""
    df = df.copy()
    high_f = df['purchase_freq'] >= f_threshold
    high_m = df['total_spend'] >= m_threshold

    conditions = [
        high_f & high_m,
        high_f & ~high_m,
        ~high_f & high_m,
        ~high_f & ~high_m
    ]
    choices = ['核心资产用户', '频次溢出用户', '金额金主用户', '大盘长尾用户']
    df['rfm_segment'] = np.select(conditions, choices, default='大盘长尾用户')
    return df

# ==================== 筛选逻辑 ====================
def filter_data_impl(df, selected_age, selected_gender, selected_category, selected_rfm):
    """实际的筛选逻辑"""
    filtered = df.copy()

    if selected_age != '全部':
        if selected_age == '18-22':
            filtered = filtered[(filtered['age'] >= 18) & (filtered['age'] <= 22)]
        elif selected_age == '23-30':
            filtered = filtered[(filtered['age'] >= 23) & (filtered['age'] <= 30)]
        elif selected_age == '31-40':
            filtered = filtered[(filtered['age'] >= 31) & (filtered['age'] <= 40)]
        elif selected_age == '40+':
            filtered = filtered[filtered['age'] > 40]

    if selected_gender != '全部':
        gender_map = {'女': 0, '男': 1}
        filtered = filtered[filtered['gender'] == gender_map[selected_gender]]

    if selected_category != '全部':
        filtered = filtered[filtered['category'] == selected_category]

    if selected_rfm != '全部':
        filtered = filtered[filtered['rfm_segment'] == selected_rfm]

    return filtered

# ==================== 带缓存的筛选函数 ====================
@st.cache_data(show_spinner=False)
def get_filtered_data(selected_age, selected_gender, selected_category, selected_rfm,
                      f_threshold, m_threshold):
    """缓存版：加载数据 → RFM分层 → 筛选。"""
    df = load_data()
    df = compute_rfm(df, f_threshold, m_threshold)
    return filter_data_impl(df, selected_age, selected_gender, selected_category, selected_rfm)

# ==================== 固定数据源标题（页面最顶端） ====================
def render_fixed_header():
    """渲染固定在页面顶端的数据源标识横幅"""
    display_text = "当前分析数据源：默认历史数据集 (active_data.csv)"

    st.markdown(
        """
        <style>
        .fixed-data-source {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background-color: #f0f2f6;
            color: #1f1f1f;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
            text-align: left;
            z-index: 999999;
            border-bottom: 1px solid #d1d5db;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        /* 避免固定横幅遮挡主内容 */
        .main .block-container {
            padding-top: 60px !important;
        }
        </style>
        <div class="fixed-data-source">""" + display_text + """</div>
        """,
        unsafe_allow_html=True
    )

# ==================== 加载当前数据（用于 RFM 阈值初始化） ====================
df = load_data()
st.sidebar.success(f"已加载 {len(df):,} 条数据")

# ==================== 侧边栏 - RFM 动态阈值控件 ====================
st.sidebar.subheader("RFM 分层阈值")

m_default = df['total_spend'].quantile(0.7)
m_max = float(df['total_spend'].max())

if st.session_state.m_threshold == 0.0:
    st.session_state.m_threshold = m_default

f_slider = st.sidebar.slider(
    "F阈值（近30天购买次数）",
    min_value=0, max_value=100,
    value=st.session_state.f_threshold,
    key="f_slider_widget"
)
st.session_state.f_threshold = f_slider

f_input = st.sidebar.number_input(
    "F阈值（精确输入）",
    min_value=0, max_value=100,
    value=st.session_state.f_threshold,
    key="f_input_widget"
)
st.session_state.f_threshold = f_input

m_slider = st.sidebar.slider(
    "M阈值（累计消费金额）",
    min_value=0.0, max_value=m_max,
    value=float(st.session_state.m_threshold),
    step=10.0,
    format="%.0f",
    key="m_slider_widget"
)
st.session_state.m_threshold = m_slider

m_input = st.sidebar.number_input(
    "M阈值（精确输入）",
    min_value=0.0, max_value=m_max,
    value=float(st.session_state.m_threshold),
    step=10.0,
    format="%.2f",
    key="m_input_widget"
)
st.session_state.m_threshold = m_input

st.sidebar.caption(f"默认M阈值（前30%分位）：¥{m_default:,.2f}")

F_THRESHOLD = st.session_state.f_threshold
M_THRESHOLD = st.session_state.m_threshold

# ==================== 主标题 ====================
render_fixed_header()
st.title("社交电商运营分析看板")
st.markdown("---")

# ==================== RFM 分层计算（前置，基于全量数据） ====================
df = compute_rfm(df, F_THRESHOLD, M_THRESHOLD)

# ==================== 顶部全局筛选器（4个） ====================
st.subheader("全局筛选")
col1, col2, col3, col4 = st.columns(4)

with col1:
    age_options = ['全部', '18-22', '23-30', '31-40', '40+']
    selected_age = st.selectbox("年龄段", options=age_options)

with col2:
    gender_options = ['全部', '女', '男']
    selected_gender = st.selectbox("性别", options=gender_options)

with col3:
    category_options = ['全部'] + sorted(df['category'].unique().tolist())
    selected_category = st.selectbox("商品品类", options=category_options)

with col4:
    rfm_options = ['全部', '核心资产用户', '频次溢出用户', '金额金主用户', '大盘长尾用户']
    selected_rfm = st.selectbox("用户价值分层", options=rfm_options)

st.markdown("---")

# ==================== 获取筛选后数据（带缓存） ====================
filtered_df = get_filtered_data(
    selected_age, selected_gender, selected_category, selected_rfm,
    F_THRESHOLD, M_THRESHOLD
)

# ==================== KPI 运营总览指标卡 ====================
st.subheader("核心指标总览")

total_users = len(filtered_df)
buyers_count = filtered_df[filtered_df['label'] == 1].shape[0]
conversion_rate = safe_rate(buyers_count, total_users)
avg_pv = filtered_df['pv_count'].mean() if total_users > 0 else 0
total_interactions = (filtered_df['like_num'].sum() + filtered_df['comment_num'].sum() +
                      filtered_df['share_num'].sum() + filtered_df['collect_num'].sum())
total_pv = filtered_df['pv_count'].sum()
avg_interaction = total_interactions / total_pv if total_pv > 0 else 0
unique_users = filtered_df['user_id'].nunique()
total_spend_sum = filtered_df['total_spend'].sum()
avg_order_value = total_spend_sum / unique_users if unique_users > 0 else 0

kpi_cols = st.columns(6)
with kpi_cols[0]:
    st.metric(label="总用户数", value=f"{total_users:,}")
with kpi_cols[1]:
    st.metric(label="购买人数", value=f"{buyers_count:,}")
with kpi_cols[2]:
    st.metric(label="购买率", value=f"{conversion_rate:.2%}")
with kpi_cols[3]:
    st.metric(label="平均浏览次数", value=f"{avg_pv:.2f}")
with kpi_cols[4]:
    st.metric(label="平均互动率", value=f"{avg_interaction:.2%}")
with kpi_cols[5]:
    st.metric(label="平均客单价", value=f"¥{avg_order_value:.2f}")

BASELINE_RATE = conversion_rate

# ==================== 通用 Lift 柱状图生成函数 ====================
def plot_lift_bar(x_col, y_col, data, title, x_label, purchase_rate_col):
    """绘制偏离度柱状图"""
    colors = ['#2ca02c' if v >= 0 else '#d62728' for v in data[y_col]]

    fig = go.Figure(go.Bar(
        x=data[x_col],
        y=data[y_col],
        marker_color=colors,
        text=[f"{v:+.1%}" for v in data[y_col]],
        textposition='outside',
        hovertemplate=(
            '%{x}<br>'
            '偏离度: %{y:+.2%}<br>'
            '绝对购买率: %{customdata:.1%}<br>'
            '<extra></extra>'
        ),
        customdata=data[purchase_rate_col]
    ))

    fig.add_hline(y=0, line_width=1, line_dash="solid", line_color="gray")

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title="购买率偏离度",
        yaxis_tickformat="+.0%",
        height=380,
        margin=dict(t=40, b=20, l=20, r=20),
    )
    y_abs_max = max(abs(data[y_col].min()), abs(data[y_col].max()), 0.02) * 1.3
    fig.update_yaxes(range=[-y_abs_max, y_abs_max])

    return fig

# ==================== 创建两个大标签页 ====================
tab1, tab2 = st.tabs(["转化链路与分层大盘", "策略矩阵下钻"])

# ================================================================
# Tab 1: 转化链路与分层大盘
# ================================================================
with tab1:
    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.markdown("#### 用户旅程转化漏斗")

        # ---------- 漏斗环节配置 ----------
        FUNNEL_ORDER = ['1. 浏览', '2. 互动', '3. 加购', '4. 领券', '5. 用券', '6. 购买']
        FUNNEL_CONFIG = {
            '1. 浏览': {
                'label': '浏览',
                'filter': None,
                'color': '#636EFA'
            },
            '2. 互动': {
                'label': '互动',
                'filter': lambda df: (
                    (df['like_num'] > 0) |
                    (df['comment_num'] > 0) |
                    (df['share_num'] > 0) |
                    (df['collect_num'] > 0) |
                    (df['is_follow_author'] == 1)
                ),
                'color': '#EF553B'
            },
            '3. 加购': {
                'label': '加购',
                'filter': lambda df: df['add2cart'] == 1,
                'color': '#00CC96'
            },
            '4. 领券': {
                'label': '领券',
                'filter': lambda df: df['coupon_received'] == 1,
                'color': '#AB63FA'
            },
            '5. 用券': {
                'label': '用券',
                'filter': lambda df: df['coupon_used'] == 1,
                'color': '#FFA15A'
            },
            '6. 购买': {
                'label': '购买',
                'filter': lambda df: df['label'] == 1,
                'color': '#19D3F3'
            }
        }

        # ---------- 前端按钮组组件 ----------
        st.markdown("**📊 自定义漏斗链路环节**（红色=启用，灰色=禁用）")
        btn_cols = st.columns(len(FUNNEL_ORDER))

        forced_steps = {'1. 浏览', '6. 购买'}

        for i, step_key in enumerate(FUNNEL_ORDER):
            is_forced = step_key in forced_steps
            is_active = step_key in st.session_state.funnel_active_steps
            btn_label = FUNNEL_CONFIG[step_key]['label']
            btn_type = "primary" if is_active else "secondary"

            if is_forced:
                # 浏览和购买强制保留，按钮禁用但显示为激活态
                btn_cols[i].button(
                    btn_label,
                    key=f"funnel_btn_{step_key}",
                    type=btn_type,
                    disabled=True,
                    use_container_width=True
                )
            else:
                if btn_cols[i].button(
                    btn_label,
                    key=f"funnel_btn_{step_key}",
                    type=btn_type,
                    use_container_width=True
                ):
                    if is_active:
                        st.session_state.funnel_active_steps.discard(step_key)
                        # 领券是用券的前置，取消领券时自动取消用券
                        if step_key == '4. 领券':
                            st.session_state.funnel_active_steps.discard('5. 用券')
                    else:
                        st.session_state.funnel_active_steps.add(step_key)
                        # 启用用券时自动启用其前置领券
                        if step_key == '5. 用券':
                            st.session_state.funnel_active_steps.add('4. 领券')
                    st.rerun()

        # 强制保留浏览和购买
        st.session_state.funnel_active_steps.update(forced_steps)

        # 按固定顺序排列
        ordered_steps = [s for s in FUNNEL_ORDER if s in st.session_state.funnel_active_steps]

        # ---------- 动态级联计算 ----------
        current_df = filtered_df
        funnel_labels = []
        funnel_counts = []
        funnel_colors = []
        prev_count = len(current_df)

        for step_key in ordered_steps:
            config = FUNNEL_CONFIG[step_key]

            # 若该环节有过滤条件，则在上一步子集上继续过滤
            if config['filter'] is not None:
                current_df = current_df[config['filter'](current_df)].copy()

            # 线性递减兜底：当前人数不得超过上一步
            count = min(len(current_df), prev_count)

            # 若触发兜底，截断子集以保证后续环节基于合法规模
            if count < len(current_df):
                current_df = current_df.head(count).copy()

            funnel_labels.append(config['label'])
            funnel_counts.append(count)
            funnel_colors.append(config['color'])
            prev_count = count

        n_total = funnel_counts[0] if funnel_counts else 0

        step_rates = []
        overall_rates = []
        for i, count in enumerate(funnel_counts):
            prev = funnel_counts[i - 1] if i > 0 else funnel_counts[0]
            step_rates.append(safe_rate(count, prev))
            overall_rates.append(safe_rate(count, n_total))

        hover_labels = [
            f"{label}<br>人数: {count:,}<br>相对上一步: {step_rates[i]:.2%}<br>整体转化率: {overall_rates[i]:.2%}"
            for i, (label, count) in enumerate(zip(funnel_labels, funnel_counts))
        ]

        # ---------- 文字位置动态适配 ----------
        # 当某层宽度占比过小时，文字自动显示在右侧空白处
        max_count = max(funnel_counts) if funnel_counts else 1
        width_ratios = [c / max_count for c in funnel_counts]
        text_positions = ['outside' if r < 0.15 else 'inside' for r in width_ratios]

        # ---------- 动态渲染漏斗图 ----------
        fig_funnel = go.Figure(go.Funnel(
            y=funnel_labels,
            x=funnel_counts,
            textposition=text_positions,
            textinfo="value+percent initial+percent previous",
            texttemplate=(
                "%{value:,}<br>"
                "整体: %{percentInitial:.1%}<br>"
                "上一步: %{percentPrevious:.1%}"
            ),
            textfont=dict(size=14),  # 统一字体大小
            hovertext=hover_labels,
            hoverinfo="text",
            marker=dict(
                color=funnel_colors,
                line=dict(width=1, color="white")
            )
        ))
        fig_funnel.update_layout(height=420, margin=dict(t=20, b=20, l=40, r=40))
        fig_funnel.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_funnel, use_container_width=True)

        # ---------- 漏斗明细表 ----------
        funnel_detail_df = pd.DataFrame({
            '步骤': funnel_labels,
            '人数': funnel_counts,
            '相对上一步转化率': [f"{r:.2%}" for r in step_rates],
            '总转化率': [f"{r:.2%}" for r in overall_rates],
            '相对上一步流失': [f"{1 - r:.2%}" for r in step_rates]
        })
        st.dataframe(funnel_detail_df, use_container_width=True, hide_index=True)

    with right_col:
        st.markdown("#### RFM 用户分层象限")

        rfm_df = filtered_df.copy()

        fig_rfm = px.scatter(
            rfm_df,
            x='purchase_freq',
            y='total_spend',
            color='rfm_segment',
            color_discrete_map={
                '核心资产用户': '#2ca02c',
                '频次溢出用户': '#1f77b4',
                '金额金主用户': '#ff7f0e',
                '大盘长尾用户': '#d62728'
            },
            hover_data={
                'purchase_freq': True,
                'total_spend': ':.2f',
                'label': True,
                'rfm_segment': False
            },
            labels={
                'purchase_freq': 'F: 近30天购买次数',
                'total_spend': 'M: 累计消费金额',
                'label': '是否购买'
            },
            title="RFM 用户价值分层象限"
        )

        fig_rfm.add_hline(
            y=M_THRESHOLD, line_dash="dash", line_color="gray",
            annotation_text=f"M阈值=¥{M_THRESHOLD:,.0f}",
            annotation_position="top right"
        )
        fig_rfm.add_vline(
            x=F_THRESHOLD, line_dash="dash", line_color="gray",
            annotation_text=f"F阈值={F_THRESHOLD}",
            annotation_position="top right"
        )

        fig_rfm.update_layout(height=420, margin=dict(t=40, b=20, l=20, r=20))
        fig_rfm.update_traces(marker=dict(size=9, opacity=0.7))
        st.plotly_chart(fig_rfm, use_container_width=True)

    st.markdown("#### 各分层购买率对比")
    rfm_summary = filtered_df.groupby('rfm_segment', observed=False).agg(
        人数=('label', 'count'),
        购买人数=('label', 'sum'),
        平均F=('purchase_freq', 'mean'),
        平均M=('total_spend', 'mean')
    ).reset_index()
    rfm_summary['购买率'] = rfm_summary.apply(
        lambda r: safe_rate(r['购买人数'], r['人数']), axis=1
    )
    rfm_summary['偏离度'] = rfm_summary['购买率'] - BASELINE_RATE
    rfm_summary['占比'] = rfm_summary['人数'] / rfm_summary['人数'].sum()

    segment_order = ['核心资产用户', '频次溢出用户', '金额金主用户', '大盘长尾用户']
    rfm_summary = assign_bin_order(rfm_summary, 'rfm_segment', segment_order)
    rfm_summary = rfm_summary.sort_values('rfm_segment')

    display_df = rfm_summary[['rfm_segment', '人数', '占比', '购买率', '偏离度', '平均F', '平均M']].copy()
    display_df.columns = ['分层', '人数', '占比', '购买率', '偏离度', '平均F', '平均M']
    display_df['占比'] = display_df['占比'].apply(lambda x: f"{x:.1%}")
    display_df['购买率'] = display_df['购买率'].apply(lambda x: f"{x:.2%}")
    display_df['偏离度'] = display_df['偏离度'].apply(lambda x: f"{x:+.2%}")
    display_df['平均F'] = display_df['平均F'].round(1)
    display_df['平均M'] = display_df['平均M'].apply(lambda x: f"¥{x:,.2f}")

    st.dataframe(display_df, use_container_width=True, hide_index=True)

# ================================================================
# Tab 2: 策略矩阵下钻
# ================================================================
with tab2:
    st.markdown("### 各维度购买率偏离度分析（Lift）")
    st.caption(f"基准线：当前筛选大盘平均购买率 = {BASELINE_RATE:.2%}")

    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["商品与价格战场", "内容与社交战场", "时间与活跃战场"])

    fdf = filtered_df.copy()

    # ============ 公用分箱计算 ============
    discount_bins = [-0.001, 0.001, 0.10, 0.20, 0.30, 0.50, float('inf')]
    discount_labels = ['0%', '(0%, 10%]', '(10%, 20%]', '(20%, 30%]', '(30%, 50%]', '>50%']
    fdf['discount_bin'] = pd.cut(fdf['discount_rate'], bins=discount_bins, labels=discount_labels, right=True)
    fdf.loc[fdf['discount_rate'] == 0, 'discount_bin'] = '0%'

    title_bins = [0, 10, 20, 30, 40, float('inf')]
    title_labels = ['≤10', '11-20', '21-30', '31-40', '>40']
    fdf['title_len_bin'] = pd.cut(fdf['title_length'], bins=title_bins, labels=title_labels, right=True)

    pv_bins = [0, 5, 10, 20, 40, float('inf')]
    pv_labels = ['1-5', '6-10', '11-20', '21-40', '40+']
    fdf['pv_bin'] = pd.cut(fdf['pv_count'], bins=pv_bins, labels=pv_labels, right=True)

    click_bins = [0, 1, 6, 24, 72, float('inf')]
    click_labels = ['≤1h', '1-6h', '6-24h', '1-3天', '>3天']
    fdf['click_bin'] = pd.cut(fdf['last_click_gap'], bins=click_bins, labels=click_labels, right=True)

    def compute_bin_stats(df, bin_col, bin_labels):
        stats = df.groupby(bin_col, observed=False).agg(
            total=('label', 'count'),
            buyers=('label', 'sum')
        ).reset_index()
        stats['purchase_rate'] = stats.apply(lambda r: safe_rate(r['buyers'], r['total']), axis=1)
        stats['lift'] = stats['purchase_rate'] - BASELINE_RATE
        stats = assign_bin_order(stats, bin_col, bin_labels)
        stats = stats.sort_values(bin_col)
        return stats

    with sub_tab1:
        c1, c2 = st.columns(2)

        discount_stats = compute_bin_stats(fdf, 'discount_bin', discount_labels)
        with c1:
            st.plotly_chart(
                plot_lift_bar('discount_bin', 'lift', discount_stats,
                              '折扣率购买率偏离度', '折扣率', 'purchase_rate'),
                use_container_width=True
            )

        cat_stats = fdf.groupby('category').agg(
            total=('label', 'count'),
            buyers=('label', 'sum')
        ).reset_index()
        cat_stats['purchase_rate'] = cat_stats.apply(lambda r: safe_rate(r['buyers'], r['total']), axis=1)
        cat_stats['lift'] = cat_stats['purchase_rate'] - BASELINE_RATE
        cat_stats = cat_stats.sort_values('lift', ascending=True)

        with c2:
            st.plotly_chart(
                plot_lift_bar('category', 'lift', cat_stats,
                              '商品品类购买率偏离度', '品类', 'purchase_rate'),
                use_container_width=True
            )

    with sub_tab2:
        c1, c2 = st.columns(2)

        title_stats = compute_bin_stats(fdf, 'title_len_bin', title_labels)
        with c1:
            st.plotly_chart(
                plot_lift_bar('title_len_bin', 'lift', title_stats,
                              '标题长度购买率偏离度', '标题长度', 'purchase_rate'),
                use_container_width=True
            )

        video_stats = fdf.groupby('has_video').agg(
            total=('label', 'count'),
            buyers=('label', 'sum')
        ).reset_index()
        video_stats['purchase_rate'] = video_stats.apply(lambda r: safe_rate(r['buyers'], r['total']), axis=1)
        video_stats['lift'] = video_stats['purchase_rate'] - BASELINE_RATE
        video_stats['has_video_label'] = video_stats['has_video'].map({0: '无视频', 1: '有视频'})

        with c2:
            st.plotly_chart(
                plot_lift_bar('has_video_label', 'lift', video_stats,
                              '有无视频购买率偏离度', '', 'purchase_rate'),
                use_container_width=True
            )

    with sub_tab3:
        c1, c2 = st.columns(2)

        pv_stats = compute_bin_stats(fdf, 'pv_bin', pv_labels)
        with c1:
            st.plotly_chart(
                plot_lift_bar('pv_bin', 'lift', pv_stats,
                              '浏览次数购买率偏离度', '浏览次数', 'purchase_rate'),
                use_container_width=True
            )

        click_stats = compute_bin_stats(fdf, 'click_bin', click_labels)
        with c2:
            st.plotly_chart(
                plot_lift_bar('click_bin', 'lift', click_stats,
                              '点击时隔购买率偏离度', '点击时隔', 'purchase_rate'),
                use_container_width=True
            )

# ==================== 数据预览 ====================
with st.expander("查看当前筛选数据预览", expanded=False):
    st.dataframe(filtered_df.head(20), use_container_width=True)
