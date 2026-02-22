import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# 设置网页标题
st.set_page_config(page_title="TGA 流动性监控站", layout="wide")

st.title("🛡️ TGA 流动性实时监控看板")
st.write(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (UTC)")

# 1. 抓取财政部官方 API 数据
@st.cache_data(ttl=3600)  # 每小时刷新一次缓存
def get_tga_data():
    url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance?filter=account_type:eq:Treasury%20General%20Account%20(TGA)&sort=-record_date&limit=10"
    response = requests.get(url)
    data = response.json()['data']
    df = pd.DataFrame(data)
    df['close_today_bal'] = df['close_today_bal'].astype(float) / 1000 # 转换为 Billion
    df['record_date'] = pd.to_datetime(df['record_date'])
    return df

try:
    df = get_tga_data()
    latest_val = df.iloc[0]['close_today_bal']
    prev_val = df.iloc[1]['close_today_bal']
    change = latest_val - prev_val
    record_date = df.iloc[0]['record_date'].strftime('%Y-%m-%d')

    # 2. 核心指标看板
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("TGA 当前余额", f"${latest_val:.2f} B", f"{change:.2f} B")
    with col2:
        gap = latest_val - 850
        st.metric("距 $850B 目标缺口", f"${gap:.2f} B", delta_color="inverse")
    with col3:
        status = "物理注水 🌊" if change < 0 else "物理抽水 🏗️"
        st.subheader(f"今日属性: {status}")

    st.divider()

    # 3. 趋势图表
    st.subheader("📈 TGA 余额变动趋势 (Billion USD)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['record_date'], y=df['close_today_bal'], mode='lines+markers', name='TGA Balance'))
    fig.add_hline(y=850, line_dash="dash", line_color="red", annotation_text="QRA 目标 $850B")
    st.plotly_chart(fig, use_container_width=True)

    # 4. 专属【TGA分析】文字版 (方便你截图或分享)
    st.subheader("📝 每日深度解读")
    st.info(f"""
    **【TGA 账户监测日报】**
    - **当前水位：** ${latest_val:.2f} B (数据日期: {record_date})
    - **变动逻辑：** 今日变动 {change:.2f} B。{'余额下降，流动性释放中。' if change < 0 else '余额上升，流动性收缩中。'}
    - **离目标缺口：** ${gap:.2f} B。目前{'仍有泄洪空间' if gap > 0 else '已跌破目标，警惕发债抽水'}。
    """)

except Exception as e:
    st.error(f"数据抓取失败，请检查财政部 API 连接。错误信息: {e}")
