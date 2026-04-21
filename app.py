import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import plotly.graph_objects as go

# ========== 页面配置 ==========
st.set_page_config(page_title="暖阳炒股模拟器", layout="wide", initial_sidebar_state="collapsed")

# ========== 自定义CSS（明亮清新主题）==========
st.markdown("""
<style>
    /* 全局背景 */
    .stApp {
        background: linear-gradient(145deg, #f5f9ff 0%, #eef2fa 100%);
    }
    /* 卡片样式 */
    .card {
        background: rgba(255,255,255,0.85);
        backdrop-filter: blur(0px);
        border-radius: 28px;
        padding: 1.4rem;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05), 0 8px 10px -6px rgba(0,0,0,0.02);
        border: 1px solid rgba(255,255,255,0.6);
        margin-bottom: 1.5rem;
        transition: all 0.2s;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 30px -12px rgba(0,0,0,0.1);
    }
    /* 指标数字 */
    .metric-value {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FF8C42, #FFB347);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        letter-spacing: -0.5px;
    }
    /* 涨跌颜色 */
    .up { color: #ff4d4d; font-weight: 600; }
    .down { color: #2ca02c; font-weight: 600; }
    /* 表格样式 */
    .stDataFrame {
        background: white;
        border-radius: 20px;
        overflow: hidden;
        border: 1px solid #e9ecef;
    }
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(90deg, #FF9F4A, #FF6B6B);
        border: none;
        border-radius: 40px;
        color: white;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
        transition: all 0.2s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stButton > button:hover {
        transform: scale(1.02);
        background: linear-gradient(90deg, #FF8C42, #FF5252);
        box-shadow: 0 5px 15px rgba(255,107,107,0.3);
    }
    /* 侧边栏美化 */
    [data-testid="stSidebar"] {
        background: rgba(255,255,255,0.92);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0,0,0,0.05);
    }
    /* 数字输入框 */
    .stNumberInput input {
        background-color: #ffffff;
        border-radius: 30px;
        border: 1px solid #FFB347;
        color: #1e293b;
        padding: 0.5rem 1rem;
    }
    /* 选择框 */
    .stSelectbox div[data-baseweb="select"] {
        background-color: white;
        border-radius: 30px;
        border: 1px solid #e2e8f0;
    }
    /* 成功/错误提示样式 */
    .success-message {
        background-color: #d1fae5;
        color: #065f46;
        padding: 1rem;
        border-radius: 20px;
        border-left: 6px solid #10b981;
        margin-bottom: 1rem;
    }
    .error-message {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 1rem;
        border-radius: 20px;
        border-left: 6px solid #ef4444;
        margin-bottom: 1rem;
    }
    /* 标题 */
    h1, h2, h3 {
        color: #1e293b;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ========== 生成股价数据 ==========
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

# ========== 大盘指数 ==========
index_data = {
    "上证指数": {"value": 4085.08, "change": 0.07},
    "深证成指": {"value": 14982.14, "change": 0.10},
    "创业板指": {"value": 3688.94, "change": 0.37}
}

# ========== 自选股 ==========
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["比亚迪", "东方财富"]

# ========== 数据持久化 ==========
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

# 记录交易并显示提示（使用 session_state 暂存提示消息）
if "toast_msg" not in st.session_state:
    st.session_state.toast_msg = None

def record_transaction(date, stock, action, qty, price, amount, success=True):
    if success:
        st.session_state.transactions.append({
            "日期": date.strftime("%Y-%m-%d"),
            "股票": stock,
            "操作": action,
            "数量": qty,
            "价格": round(price, 2),
            "金额": round(amount, 2)
        })
        auto_save()
        st.session_state.toast_msg = f"✅ {action} {qty} 股 {stock} 成功！花费/获得 {amount:.2f} 元"
    else:
        st.session_state.toast_msg = f"❌ {action} 失败：{'现金不足' if action=='买入' else '持股不足'}"

# 显示提示消息
if st.session_state.toast_msg:
    if "✅" in st.session_state.toast_msg:
        st.markdown(f'<div class="success-message">{st.session_state.toast_msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="error-message">{st.session_state.toast_msg}</div>', unsafe_allow_html=True)
    st.session_state.toast_msg = None

# ========== 计算总资产 ==========
def get_total_asset(date):
    stock_val = sum(st.session_state.holdings[s] * get_price(date, s) for s in stocks)
    return st.session_state.cash + stock_val

latest_date = end_date
total_asset = get_total_asset(latest_date)
profit = total_asset - 5000
profit_rate = (profit / 5000) * 100
market_value = total_asset - st.session_state.cash

# ========== 顶部指标卡片 ==========
st.markdown(f"""
<div style="display: flex; justify-content: space-between; gap: 1rem; margin-bottom: 2rem;">
    <div class="card" style="flex:1; text-align:center;">
        <div style="font-size:0.9rem; color:#475569;">总资产</div>
        <div class="metric-value">{total_asset:.2f} 元</div>
    </div>
    <div class="card" style="flex:1; text-align:center;">
        <div style="font-size:0.9rem; color:#475569;">可用资金</div>
        <div class="metric-value">{st.session_state.cash:.2f} 元</div>
    </div>
    <div class="card" style="flex:1; text-align:center;">
        <div style="font-size:0.9rem; color:#475569;">持仓市值</div>
        <div class="metric-value">{market_value:.2f} 元</div>
    </div>
    <div class="card" style="flex:1; text-align:center;">
        <div style="font-size:0.9rem; color:#475569;">总收益</div>
        <div class="metric-value" style="color: {'#ff4d4d' if profit>=0 else '#2ca02c'};">{profit:+.2f} 元</div>
        <div style="font-size:0.8rem; color:#475569;">({profit_rate:+.2f}%)</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ========== 两列布局 ==========
col_left, col_right = st.columns([0.6, 0.4], gap="large")

with col_left:
    # 大盘指数
    with st.container():
        st.markdown('<div class="card"><h3 style="margin-top:0;">📊 市场概览</h3>', unsafe_allow_html=True)
        idx_cols = st.columns(3)
        for i, (name, data) in enumerate(index_data.items()):
            color = "#ff4d4d" if data["change"] >= 0 else "#2ca02c"
            sign = "+" if data["change"] >= 0 else ""
            idx_cols[i].markdown(f"""
            <div style="text-align:center;">
                <div style="font-size:1rem; font-weight:500;">{name}</div>
                <div style="font-size:1.8rem; font-weight:700;">{data['value']:.2f}</div>
                <div style="color:{color};">{sign}{data['change']:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 自选股
    with st.container():
        st.markdown('<div class="card"><h3 style="margin-top:0;">⭐ 自选股</h3>', unsafe_allow_html=True)
        # 添加自选股（修复下拉选项）
        available_stocks = [s for s in stocks if s not in st.session_state.watchlist]
        if available_stocks:
            add_stock = st.selectbox("添加股票", available_stocks, key="add_watch_select")
            if st.button("➕ 添加", key="add_watch_btn"):
                st.session_state.watchlist.append(add_stock)
                st.rerun()
        else:
            st.info("所有股票已在自选股中")
        # 显示自选股表格
        if st.session_state.watchlist:
            for stock in st.session_state.watchlist:
                price = get_price(latest_date, stock)
                prev_date = date_list[-2] if len(date_list)>1 else latest_date
                prev_price = get_price(prev_date, stock)
                change_pct = (price - prev_price) / prev_price * 100 if prev_price else 0
                color = "#ff4d4d" if change_pct >= 0 else "#2ca02c"
                sign = "+" if change_pct >= 0 else ""
                col1, col2, col3, col4 = st.columns([2,1,1,1])
                col1.write(stock)
                col2.write(f"{price:.2f}")
                col3.markdown(f'<span style="color:{color};">{sign}{change_pct:.2f}%</span>', unsafe_allow_html=True)
                if col4.button("买入", key=f"quick_buy_{stock}"):
                    st.session_state.quick_buy_stock = stock
                    st.rerun()
            # 删除自选股（可选）
            del_stock = st.selectbox("删除自选股", st.session_state.watchlist, key="del_watch_select")
            if st.button("🗑️ 删除", key="del_watch_btn"):
                st.session_state.watchlist.remove(del_stock)
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
        
        default_stock = getattr(st.session_state, "quick_buy_stock", "招商银行")
        stock_choice = st.selectbox("股票", stocks, index=stocks.index(default_stock) if default_stock in stocks else 0)
        action = st.radio("方向", ["买入", "卖出"], horizontal=True)
        qty = st.number_input("数量（股）", min_value=1, step=1, value=1, key="trade_qty")
        
        price = get_price(selected_date, stock_choice)
        st.markdown(f"<div style='text-align:center; margin:0.5rem 0;'><span style='font-size:1.8rem; font-weight:700; color:#FF8C42;'>{price:.2f}</span> 元</div>", unsafe_allow_html=True)
        
        if st.button("确认交易", use_container_width=True):
            total_cost = price * qty
            if action == "买入":
                if total_cost <= st.session_state.cash:
                    st.session_state.cash -= total_cost
                    st.session_state.holdings[stock_choice] += qty
                    record_transaction(selected_date, stock_choice, "买入", qty, price, total_cost, success=True)
                    st.rerun()
                else:
                    record_transaction(selected_date, stock_choice, "买入", qty, price, total_cost, success=False)
                    st.rerun()
            else:
                if qty <= st.session_state.holdings[stock_choice]:
                    st.session_state.cash += total_cost
                    st.session_state.holdings[stock_choice] -= qty
                    record_transaction(selected_date, stock_choice, "卖出", qty, price, total_cost, success=True)
                    st.rerun()
                else:
                    record_transaction(selected_date, stock_choice, "卖出", qty, price, total_cost, success=False)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ========== 下方标签页 ==========
tab1, tab2, tab3 = st.tabs(["💼 我的持仓", "📈 资产曲线", "📜 交易明细"])

with tab1:
    holdings_list = []
    for stock in stocks:
        qty = st.session_state.holdings[stock]
        if qty > 0:
            price = get_price(latest_date, stock)
            market_val = qty * price
            holdings_list.append({"股票": stock, "持股数量": qty, "最新价": f"{price:.2f}", "市值": f"{market_val:.2f}"})
    if holdings_list:
        st.dataframe(pd.DataFrame(holdings_list), use_container_width=True, hide_index=True)
    else:
        st.info("📭 暂无持仓，去买入一些股票吧")

with tab2:
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
        fig.add_trace(go.Scatter(x=hist_df["日期"], y=hist_df["总资产"], mode="lines+markers", line=dict(color="#FF8C42", width=3), marker=dict(size=6, color="#FFB347")))
        fig.update_layout(title="总资产变化趋势", xaxis_title="日期", yaxis_title="总资产 (元)", plot_bgcolor="white", paper_bgcolor="white", font_color="#1e293b", xaxis=dict(gridcolor="#e2e8f0"), yaxis=dict(gridcolor="#e2e8f0"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 暂无交易记录，完成一笔交易后曲线会自动出现")

with tab3:
    if st.session_state.transactions:
        df_trans = pd.DataFrame(st.session_state.transactions)
        st.dataframe(df_trans, use_container_width=True, hide_index=True)
        csv = df_trans.to_csv(index=False).encode('utf-8')
        st.download_button("📥 导出CSV", csv, "transactions.csv", "text/csv")
    else:
        st.info("📜 暂无交易记录")

# ========== 侧边栏结算 ==========
with st.sidebar:
    st.markdown("### 🎯 模拟结算")
    if st.button("结束模拟并计算最终收益"):
        final_total = get_total_asset(latest_date)
        profit = final_total - 5000
        profit_rate = (profit / 5000) * 100
        st.success(f"✨ 总资产：{final_total:.2f} 元\n✨ 收益：{profit:+.2f} 元\n✨ 收益率：{profit_rate:+.2f}%")
        st.balloons()
