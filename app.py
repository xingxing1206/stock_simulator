import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# ========== 页面配置 ==========
st.set_page_config(page_title="极智炒股模拟器", layout="wide", initial_sidebar_state="collapsed")

# ========== 自定义CSS（惊艳深色主题）==========
st.markdown("""
<style>
    /* 全局背景 */
    .stApp {
        background: linear-gradient(135deg, #0b0f1c 0%, #1a1f2f 100%);
        color: #eef2ff;
    }
    /* 卡片样式 */
    .card {
        background: rgba(20, 25, 45, 0.75);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 1.5rem;
    }
    /* 指标数字 */
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FFD166, #FF9F4A);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    /* 涨跌颜色 */
    .up { color: #ff4d4d; font-weight: 600; }
    .down { color: #2ca02c; font-weight: 600; }
    /* 表格样式 */
    .stDataFrame {
        background: rgba(0,0,0,0.3);
        border-radius: 16px;
        overflow: hidden;
    }
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(90deg, #FF6B6B, #FF8E53);
        border: none;
        border-radius: 40px;
        color: white;
        font-weight: 600;
        padding: 0.5rem 1.2rem;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(255,107,107,0.5);
    }
    /* 侧边栏美化 */
    [data-testid="stSidebar"] {
        background: rgba(10, 14, 23, 0.95);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    /* 数字输入框 */
    .stNumberInput input {
        background-color: #1e2438;
        border-radius: 20px;
        border: 1px solid #ff8e53;
        color: white;
    }
    /* 选择框 */
    .stSelectbox div[data-baseweb="select"] {
        background-color: #1e2438;
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ========== 生成股价数据（2026-04-10 至 2026-05-29）==========
start_date = datetime(2026, 4, 10)
end_date = datetime(2026, 5, 29)
date_list = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

np.random.seed(42)
stocks = ["招商银行", "贵州茅台", "宁德时代", "比亚迪", "东方财富"]
base_prices = {"招商银行": 35.0, "贵州茅台": 1650.0, "宁德时代": 180.0, "比亚迪": 230.0, "东方财富": 25.0}
price_data = {}
for stock in stocks:
    prices = [base_prices[stock]]
    for _ in range(len(date_list)-1):
        change = np.random.uniform(-0.03, 0.03)
        prices.append(max(prices[-1] * (1 + change), 0.5))
    price_data[stock] = prices
df_prices = pd.DataFrame(price_data, index=date_list)

def get_price(date, stock):
    return df_prices.loc[date, stock]

# ========== 大盘指数模拟 ==========
index_data = {
    "上证指数": {"value": 4085.08, "change": 0.07},
    "深证成指": {"value": 14982.14, "change": 0.10},
    "创业板指": {"value": 3688.94, "change": 0.37}
}

# ========== 自选股管理 ==========
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["比亚迪", "东方财富"]

# ========== 数据持久化（本地文件）==========
DATA_FILE = "user_data.json"
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("cash", 5000.0), data.get("holdings", {s:0 for s in stocks}), data.get("transactions", [])
        except:
            pass
    return 5000.0, {s:0 for s in stocks}, []
def save_data(cash, holdings, transactions):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"cash": cash, "holdings": holdings, "transactions": transactions}, f, ensure_ascii=False, indent=2)

if "cash" not in st.session_state:
    cash, holdings, transactions = load_data()
    st.session_state.cash = cash
    st.session_state.holdings = holdings
    st.session_state.transactions = transactions

def auto_save():
    save_data(st.session_state.cash, st.session_state.holdings, st.session_state.transactions)

def record_transaction(date, stock, action, qty, price, amount):
    st.session_state.transactions.append({
        "日期": date.strftime("%Y-%m-%d"),
        "股票": stock,
        "操作": action,
        "数量": qty,
        "价格": round(price, 2),
        "金额": round(amount, 2)
    })
    auto_save()

# ========== 计算总资产和收益 ==========
def get_total_asset(date):
    stock_val = sum(st.session_state.holdings[s] * get_price(date, s) for s in stocks)
    return st.session_state.cash + stock_val

latest_date = end_date
total_asset = get_total_asset(latest_date)
profit = total_asset - 5000
profit_rate = (profit / 5000) * 100

# ========== 顶部指标卡片 ==========
st.markdown("""
<div style="display: flex; justify-content: space-between; gap: 1rem; margin-bottom: 2rem;">
    <div class="card" style="flex:1; text-align:center;">
        <div style="font-size:0.9rem; opacity:0.7;">总资产</div>
        <div class="metric-value">{:.2f} 元</div>
    </div>
    <div class="card" style="flex:1; text-align:center;">
        <div style="font-size:0.9rem; opacity:0.7;">可用资金</div>
        <div class="metric-value">{:.2f} 元</div>
    </div>
    <div class="card" style="flex:1; text-align:center;">
        <div style="font-size:0.9rem; opacity:0.7;">持仓市值</div>
        <div class="metric-value">{:.2f} 元</div>
    </div>
    <div class="card" style="flex:1; text-align:center;">
        <div style="font-size:0.9rem; opacity:0.7;">总收益</div>
        <div class="metric-value" style="color: {};">{:.2f} 元</div>
        <div style="font-size:0.8rem;">({:.2f}%)</div>
    </div>
</div>
""".format(
    total_asset,
    st.session_state.cash,
    total_asset - st.session_state.cash,
    "#ff4d4d" if profit >= 0 else "#2ca02c",
    profit,
    profit_rate
), unsafe_allow_html=True)

# ========== 两列布局：大盘+自选 / 交易区 ==========
col_left, col_right = st.columns([0.6, 0.4], gap="large")

with col_left:
    # 大盘指数卡片
    with st.container():
        st.markdown('<div class="card"><h3 style="margin-top:0;">📊 市场概览</h3>', unsafe_allow_html=True)
        index_cols = st.columns(3)
        for i, (name, data) in enumerate(index_data.items()):
            color = "#ff4d4d" if data["change"] >= 0 else "#2ca02c"
            sign = "+" if data["change"] >= 0 else ""
            index_cols[i].markdown(f"""
            <div style="text-align:center;">
                <div style="font-size:1rem;">{name}</div>
                <div style="font-size:1.8rem; font-weight:700;">{data['value']:.2f}</div>
                <div style="color:{color};">{sign}{data['change']:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 自选股板块
    with st.container():
        st.markdown('<div class="card"><h3 style="margin-top:0;">⭐ 自选股</h3>', unsafe_allow_html=True)
        # 添加自选股
        add_stock = st.selectbox("添加股票", [s for s in stocks if s not in st.session_state.watchlist], key="add_watch")
        if st.button("➕ 添加", key="add_watch_btn"):
            if add_stock and add_stock not in st.session_state.watchlist:
                st.session_state.watchlist.append(add_stock)
                st.rerun()
        # 显示自选股表格
        if st.session_state.watchlist:
            watch_data = []
            for stock in st.session_state.watchlist:
                price = get_price(latest_date, stock)
                # 涨跌幅模拟（相对于前一天）
                prev_date = date_list[-2] if len(date_list)>1 else latest_date
                prev_price = get_price(prev_date, stock)
                change_pct = (price - prev_price) / prev_price * 100 if prev_price else 0
                color = "#ff4d4d" if change_pct >= 0 else "#2ca02c"
                sign = "+" if change_pct >= 0 else ""
                watch_data.append({
                    "股票": stock,
                    "现价": f"{price:.2f}",
                    "涨跌幅": f'<span style="color:{color};">{sign}{change_pct:.2f}%</span>',
                    "操作": f'<button class="buy-btn" data-stock="{stock}">买入</button>'
                })
            # 使用HTML表格（因为需要按钮交互，但streamlit按钮不能直接嵌入，这里仅展示，买入按钮单独处理）
            for w in watch_data:
                col1, col2, col3, col4 = st.columns([2,1,1,1])
                col1.write(w["股票"])
                col2.write(w["现价"])
                col3.markdown(w["涨跌幅"], unsafe_allow_html=True)
                if col4.button("买入", key=f"buy_{w['股票']}"):
                    # 快速买入逻辑：跳转到交易区，预设股票
                    st.session_state.quick_buy_stock = w["股票"]
                    st.rerun()
        else:
            st.info("暂无自选股，请添加")
        st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    # 交易卡片
    with st.container():
        st.markdown('<div class="card"><h3 style="margin-top:0;">💰 快捷交易</h3>', unsafe_allow_html=True)
        selected_date = st.date_input("交易日", value=start_date, min_value=start_date, max_value=end_date, key="trade_date")
        selected_date = pd.Timestamp(selected_date)
        
        # 预设股票（支持快速买入）
        default_stock = getattr(st.session_state, "quick_buy_stock", "招商银行")
        stock_choice = st.selectbox("股票", stocks, index=stocks.index(default_stock) if default_stock in stocks else 0)
        action = st.radio("方向", ["买入", "卖出"], horizontal=True)
        qty = st.number_input("数量（股）", min_value=1, step=1, value=1, key="trade_qty")
        
        price = get_price(selected_date, stock_choice)
        st.markdown(f"<div style='text-align:center; margin:1rem 0;'><span style='font-size:1.5rem; font-weight:bold;'>{price:.2f}</span> 元</div>", unsafe_allow_html=True)
        
        if st.button("确认交易", use_container_width=True):
            total_cost = price * qty
            if action == "买入":
                if total_cost <= st.session_state.cash:
                    st.session_state.cash -= total_cost
                    st.session_state.holdings[stock_choice] += qty
                    record_transaction(selected_date, stock_choice, "买入", qty, price, total_cost)
                    st.success(f"✅ 买入 {qty} 股 {stock_choice} 成功")
                    st.rerun()
                else:
                    st.error("现金不足")
            else:
                if qty <= st.session_state.holdings[stock_choice]:
                    st.session_state.cash += total_cost
                    st.session_state.holdings[stock_choice] -= qty
                    record_transaction(selected_date, stock_choice, "卖出", qty, price, total_cost)
                    st.success(f"✅ 卖出 {qty} 股 {stock_choice} 成功")
                    st.rerun()
                else:
                    st.error("持股不足")
        st.markdown('</div>', unsafe_allow_html=True)

# ========== 下方区域：持仓表格 + 资产曲线 + 交易记录 ==========
tab1, tab2, tab3 = st.tabs(["💼 我的持仓", "📈 资产曲线", "📜 交易明细"])

with tab1:
    holdings_list = []
    for stock in stocks:
        qty = st.session_state.holdings[stock]
        if qty > 0:
            price = get_price(latest_date, stock)
            market_val = qty * price
            holdings_list.append({"股票": stock, "持股数量": qty, "最新价": price, "市值": market_val})
    if holdings_list:
        df_hold = pd.DataFrame(holdings_list)
        df_hold["最新价"] = df_hold["最新价"].map("{:.2f}".format)
        df_hold["市值"] = df_hold["市值"].map("{:.2f}".format)
        st.dataframe(df_hold, use_container_width=True, hide_index=True)
    else:
        st.info("暂无持仓，快去买入吧")

with tab2:
    # 绘制资产曲线（基于交易记录）
    if st.session_state.transactions:
        history = [(start_date, 5000.0)]
        cash_temp = 5000.0
        holdings_temp = {s:0 for s in stocks}
        for t in sorted(st.session_state.transactions, key=lambda x: x["日期"]):
            date = pd.Timestamp(t["日期"])
            stock = t["股票"]
            action = t["操作"]
            qty = t["数量"]
            price = t["价格"]
            if action == "买入":
                cash_temp -= price * qty
                holdings_temp[stock] += qty
            else:
                cash_temp += price * qty
                holdings_temp[stock] -= qty
            stock_val = sum(holdings_temp[s] * get_price(date, s) for s in stocks)
            total = cash_temp + stock_val
            history.append((date, total))
        hist_df = pd.DataFrame(history, columns=["日期", "总资产"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist_df["日期"], y=hist_df["总资产"], mode="lines+markers", line=dict(color="#FF8E53", width=3), marker=dict(size=6)))
        fig.update_layout(title="总资产变化趋势", xaxis_title="日期", yaxis_title="总资产 (元)", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white", xaxis=dict(gridcolor="rgba(255,255,255,0.2)"), yaxis=dict(gridcolor="rgba(255,255,255,0.2)"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无交易记录，无法绘制曲线")

with tab3:
    if st.session_state.transactions:
        df_trans = pd.DataFrame(st.session_state.transactions)
        st.dataframe(df_trans, use_container_width=True, hide_index=True)
        csv = df_trans.to_csv(index=False).encode('utf-8')
        st.download_button("导出CSV", csv, "transactions.csv", "text/csv")
    else:
        st.info("暂无交易记录")

# ========== 侧边栏结算按钮 ==========
with st.sidebar:
    st.markdown("### 🎯 模拟结算")
    if st.button("结束模拟并计算最终收益"):
        final_total = get_total_asset(latest_date)
        profit = final_total - 5000
        profit_rate = (profit / 5000) * 100
        st.success(f"总资产：{final_total:.2f} 元 | 收益：{profit:+.2f} 元 | 收益率：{profit_rate:+.2f}%")
        st.balloons()
