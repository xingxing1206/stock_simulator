import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(page_title="模拟炒股系统", layout="wide", initial_sidebar_state="collapsed")

# ========== 高级CSS ==========
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #f0f4ff 0%, #e8edfc 100%); }
.glass-card {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(10px);
    border-radius: 28px;
    padding: 1.5rem;
    box-shadow: 0 8px 32px rgba(31,38,135,0.1);
    margin-bottom: 1.5rem;
}
.metric-value {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #FF8C42, #FF6B6B);
    -webkit-background-clip: text;
    color: transparent;
}
.stButton>button {
    background: linear-gradient(90deg, #FF8C42, #FF6B6B);
    border: none;
    border-radius: 40px;
    color: white;
    font-weight: 600;
}
.custom-success { background: #d1fae5; color: #065f46; padding: 0.8rem; border-radius: 40px; }
.custom-error { background: #fee2e2; color: #991b1b; padding: 0.8rem; border-radius: 40px; }
</style>
""", unsafe_allow_html=True)

# ========== 生成真实交易日历（从现在往前推，直到2026-04-10）==========
def generate_trading_days(start_dt, end_dt):
    """生成所有交易日（周一至周五），跳过周末"""
    days = []
    current = start_dt
    while current <= end_dt:
        if current.weekday() < 5:  # 周一=0, 周五=4
            days.append(current)
        current += timedelta(days=1)
    return days

# 作业要求起始日期2026-04-10，结束日期为今天（实际日期）
start_date = datetime(2026, 4, 10)
end_date = datetime.today()  # 今天
trading_days = generate_trading_days(start_date, end_date)
if not trading_days:
    trading_days = [start_date]  # 兜底

# 股票列表及初始价格
stocks = ["招商银行", "贵州茅台", "宁德时代", "比亚迪", "东方财富"]
base_prices = {"招商银行": 35.0, "贵州茅台": 1650.0, "宁德时代": 180.0, "比亚迪": 230.0, "东方财富": 25.0}

# 生成每个交易日的收盘价（基于随机游走，但每个品种独立）
np.random.seed(42)  # 固定种子，保证每次启动价格序列一致
price_data = {stock: [] for stock in stocks}
for stock in stocks:
    prices = [base_prices[stock]]
    for i in range(1, len(trading_days)):
        change = np.random.uniform(-0.03, 0.03)
        prices.append(max(prices[-1] * (1 + change), 0.5))
    price_data[stock] = prices
df_prices = pd.DataFrame(price_data, index=trading_days)

def get_price(date, stock):
    return df_prices.loc[date, stock]

# ========== 初始化 session state ==========
if "cash" not in st.session_state:
    st.session_state.cash = 5000.0
if "holdings" not in st.session_state:
    st.session_state.holdings = {s:0 for s in stocks}
if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "toast_msg" not in st.session_state:
    st.session_state.toast_msg = None

def record_transaction(date, stock, action, qty, price, amount, success=True):
    if success:
        st.session_state.transactions.append({
            "日期": date.strftime("%Y-%m-%d"),
            "股票": stock,
            "操作": action,
            "数量": qty,
            "价格": round(price,2),
            "金额": round(amount,2)
        })
        st.session_state.toast_msg = f"✅ {action} {qty}股 {stock} 成功！{'花费' if action=='买入' else '获得'} {amount:.2f}元"
    else:
        st.session_state.toast_msg = f"❌ {action} 失败：{'现金不足' if action=='买入' else '持股不足'}"

if st.session_state.toast_msg:
    if "✅" in st.session_state.toast_msg:
        st.markdown(f'<div class="custom-success">{st.session_state.toast_msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="custom-error">{st.session_state.toast_msg}</div>', unsafe_allow_html=True)
    st.session_state.toast_msg = None

# ========== 实时资产计算 ==========
latest_date = trading_days[-1]  # 最新交易日
total_market = sum(st.session_state.holdings[s] * get_price(latest_date, s) for s in stocks)
total_asset = st.session_state.cash + total_market
profit = total_asset - 5000
profit_rate = (profit/5000)*100

# 顶部指标
st.markdown(f"""
<div style="display:flex; gap:1rem;">
    <div class="glass-card" style="flex:1; text-align:center;">💰 总资产<br><span class="metric-value">{total_asset:.2f}</span>元</div>
    <div class="glass-card" style="flex:1; text-align:center;">💵 可用资金<br><span class="metric-value">{st.session_state.cash:.2f}</span>元</div>
    <div class="glass-card" style="flex:1; text-align:center;">📈 总收益<br><span class="metric-value" style="color:{'#ff4d4d' if profit>=0 else '#2ca02c'};">{profit:+.2f}</span>元 ({profit_rate:+.2f}%)</div>
</div>
""", unsafe_allow_html=True)

# ========== 交易区域 ==========
st.markdown('<div class="glass-card"><h3>⚡ 实时交易（真实日历）</h3>', unsafe_allow_html=True)

# 日期选择器：只显示交易日，默认最新
selected_index = len(trading_days)-1
selected_date = st.selectbox("📅 选择交易日（历史日期）", trading_days, index=selected_index, format_func=lambda x: x.strftime("%Y-%m-%d %A"))
selected_date = pd.Timestamp(selected_date)

st.subheader(f"📊 {selected_date.strftime('%Y-%m-%d')} 收盘价")
cols = st.columns(len(stocks))
for i, stock in enumerate(stocks):
    price = get_price(selected_date, stock)
    cols[i].metric(stock, f"{price:.2f} 元")

col1, col2, col3 = st.columns(3)
with col1:
    stock_choice = st.selectbox("股票", stocks)
with col2:
    action = st.radio("操作", ["买入","卖出"], horizontal=True)
with col3:
    qty = st.number_input("数量（股）", min_value=1, step=1, value=1)

if st.button("✅ 确认交易", use_container_width=True):
    price = get_price(selected_date, stock_choice)
    total = price * qty
    if action == "买入":
        if total <= st.session_state.cash:
            st.session_state.cash -= total
            st.session_state.holdings[stock_choice] += qty
            record_transaction(selected_date, stock_choice, "买入", qty, price, total, True)
            st.rerun()
        else:
            record_transaction(selected_date, stock_choice, "买入", qty, price, total, False)
            st.rerun()
    else:
        if qty <= st.session_state.holdings[stock_choice]:
            st.session_state.cash += total
            st.session_state.holdings[stock_choice] -= qty
            record_transaction(selected_date, stock_choice, "卖出", qty, price, total, True)
            st.rerun()
        else:
            record_transaction(selected_date, stock_choice, "卖出", qty, price, total, False)
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ========== 持仓 / 曲线 / 记录 ==========
tab1, tab2, tab3 = st.tabs(["💼 我的持仓", "📈 资产曲线", "📜 交易明细"])
with tab1:
    holdings_list = []
    for s in stocks:
        q = st.session_state.holdings[s]
        if q>0:
            p = get_price(latest_date, s)
            holdings_list.append({"股票":s, "持股数量":q, "最新价":f"{p:.2f}", "市值":f"{q*p:.2f}"})
    if holdings_list:
        st.dataframe(pd.DataFrame(holdings_list), use_container_width=True)
    else:
        st.info("暂无持仓")
with tab2:
    if st.session_state.transactions:
        history = [(trading_days[0], 5000.0)]
        cash_tmp = 5000.0
        hold_tmp = {s:0 for s in stocks}
        for t in sorted(st.session_state.transactions, key=lambda x: x["日期"]):
            date = pd.Timestamp(t["日期"])
            s = t["股票"]
            act = t["操作"]
            q = t["数量"]
            pr = t["价格"]
            if act == "买入":
                cash_tmp -= pr * q
                hold_tmp[s] += q
            else:
                cash_tmp += pr * q
                hold_tmp[s] -= q
            sv = sum(hold_tmp[ss] * get_price(date, ss) for ss in stocks)
            history.append((date, cash_tmp + sv))
        df_hist = pd.DataFrame(history, columns=["日期","总资产"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_hist["日期"], y=df_hist["总资产"], mode="lines+markers", line=dict(color="#FF8C42", width=3)))
        fig.update_layout(title="总资产变化趋势", xaxis_title="日期", yaxis_title="总资产 (元)", plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无交易记录")
with tab3:
    if st.session_state.transactions:
        df_trans = pd.DataFrame(st.session_state.transactions)
        st.dataframe(df_trans, use_container_width=True)
        csv = df_trans.to_csv(index=False).encode('utf-8')
        st.download_button("📥 导出CSV", csv, "transactions.csv")
    else:
        st.info("暂无交易记录")

# 侧边栏结算
with st.sidebar:
    st.markdown("### 🎯 模拟结算")
    if st.button("结束模拟并计算最终收益"):
        st.success(f"✨ 总资产：{total_asset:.2f} 元\n✨ 收益：{profit:+.2f} 元\n✨ 收益率：{profit_rate:+.2f}%")
        st.balloons()
