import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import json

st.set_page_config(page_title="暖阳炒股模拟器", layout="wide", initial_sidebar_state="collapsed")

# ========== 自定义CSS（明亮清新主题）==========
st.markdown("""
<style>
    .stApp { background: linear-gradient(145deg, #f5f9ff 0%, #eef2fa 100%); }
    .card {
        background: rgba(255,255,255,0.85);
        border-radius: 28px;
        padding: 1.4rem;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
        border: 1px solid rgba(255,255,255,0.6);
        margin-bottom: 1.5rem;
    }
    .metric-value {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FF8C42, #FFB347);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .up { color: #ff4d4d; font-weight: 600; }
    .down { color: #2ca02c; font-weight: 600; }
    .stButton > button {
        background: linear-gradient(90deg, #FF9F4A, #FF6B6B);
        border: none;
        border-radius: 40px;
        color: white;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        background: linear-gradient(90deg, #FF8C42, #FF5252);
    }
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
</style>
""", unsafe_allow_html=True)

# ========== 生成股价数据（固定）==========
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

# ========== 纯前端 localStorage 支持（无额外依赖）==========
# 注入 JS 代码，实现数据自动保存和加载
js_code = """
<script>
function saveToLocalStorage(data) {
    localStorage.setItem('stock_simulator_data', JSON.stringify(data));
}
function loadFromLocalStorage() {
    var data = localStorage.getItem('stock_simulator_data');
    if (data) {
        var input = document.getElementById('hidden_storage_input');
        if (input) {
            input.value = data;
            input.dispatchEvent(new Event('input', {bubbles: true}));
        }
    }
}
window.onload = loadFromLocalStorage;
// 监听 Streamlit 渲染，将当前 session_state 保存到 localStorage
function syncToLocalStorage() {
    var dataDiv = document.getElementById('session_data_content');
    if (dataDiv && dataDiv.innerText) {
        try {
            var data = JSON.parse(dataDiv.innerText);
            saveToLocalStorage(data);
        } catch(e) {}
    }
}
setInterval(syncToLocalStorage, 500);
</script>
"""
st.markdown(js_code, unsafe_allow_html=True)

# 隐藏的 div 用于存放序列化的 session_state（供 JS 读取）
serialized_data = json.dumps({
    "cash": st.session_state.get("cash", 5000.0),
    "holdings": st.session_state.get("holdings", {s:0 for s in stocks}),
    "transactions": st.session_state.get("transactions", []),
    "watchlist": st.session_state.get("watchlist", ["比亚迪", "东方财富"])
})
st.markdown(f'<div id="session_data_content" style="display:none;">{serialized_data}</div>', unsafe_allow_html=True)

# 隐藏的 textarea 用于接收从 localStorage 加载的数据
stored_data = st.text_area("", key="hidden_storage_input", label_visibility="collapsed", value="")
st.markdown('<style>#hidden_storage_input { display: none; }</style>', unsafe_allow_html=True)

# 恢复数据
if stored_data and stored_data.strip():
    try:
        restored = json.loads(stored_data)
        if "cash" not in st.session_state:
            st.session_state.cash = restored.get("cash", 5000.0)
            st.session_state.holdings = restored.get("holdings", {s:0 for s in stocks})
            st.session_state.transactions = restored.get("transactions", [])
            st.session_state.watchlist = restored.get("watchlist", ["比亚迪", "东方财富"])
    except:
        pass

# 初始化 session_state 默认值
if "cash" not in st.session_state:
    st.session_state.cash = 5000.0
if "holdings" not in st.session_state:
    st.session_state.holdings = {s:0 for s in stocks}
if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["比亚迪", "东方财富"]
if "toast_msg" not in st.session_state:
    st.session_state.toast_msg = None
if "quick_buy_stock" not in st.session_state:
    st.session_state.quick_buy_stock = "招商银行"

# 辅助函数：交易记录
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
        st.session_state.toast_msg = f"✅ {action} {qty} 股 {stock} 成功！{'花费' if action=='买入' else '获得'} {amount:.2f} 元"
    else:
        st.session_state.toast_msg = f"❌ {action} 失败：{'现金不足' if action=='买入' else '持股不足'}"

# 显示提示消息
if st.session_state.toast_msg:
    if "✅" in st.session_state.toast_msg:
        st.markdown(f'<div class="success-message">{st.session_state.toast_msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="error-message">{st.session_state.toast_msg}</div>', unsafe_allow_html=True)
    st.session_state.toast_msg = None

# 计算总资产
def get_total_asset(date):
    stock_val = sum(st.session_state.holdings[s] * get_price(date, s) for s in stocks)
    return st.session_state.cash + stock_val

latest_date = end_date
total_asset = get_total_asset(latest_date)
profit = total_asset - 5000
profit_rate = (profit / 5000) * 100
market_value = total_asset - st.session_state.cash

# 顶部指标卡片
st.markdown(f"""
<div style="display: flex; justify-content: space-between; gap: 1rem; margin-bottom: 2rem;">
    <div class="card" style="flex:1; text-align:center;"><div style="font-size:0.9rem; color:#475569;">总资产</div><div class="metric-value">{total_asset:.2f} 元</div></div>
    <div class="card" style="flex:1; text-align:center;"><div style="font-size:0.9rem; color:#475569;">可用资金</div><div class="metric-value">{st.session_state.cash:.2f} 元</div></div>
    <div class="card" style="flex:1; text-align:center;"><div style="font-size:0.9rem; color:#475569;">持仓市值</div><div class="metric-value">{market_value:.2f} 元</div></div>
    <div class="card" style="flex:1; text-align:center;"><div style="font-size:0.9rem; color:#475569;">总收益</div><div class="metric-value" style="color: {'#ff4d4d' if profit>=0 else '#2ca02c'};">{profit:+.2f} 元</div><div style="font-size:0.8rem;">({profit_rate:+.2f}%)</div></div>
</div>
""", unsafe_allow_html=True)

# 两列布局
col_left, col_right = st.columns([0.6, 0.4], gap="large")

with col_left:
    # 大盘指数
    with st.container():
        st.markdown('<div class="card"><h3 style="margin-top:0;">📊 市场概览</h3>', unsafe_allow_html=True)
        index_data = {"上证指数": (4085.08, 0.07), "深证成指": (14982.14, 0.10), "创业板指": (3688.94, 0.37)}
        cols = st.columns(3)
        for i, (name, (value, chg)) in enumerate(index_data.items()):
            color = "#ff4d4d" if chg >= 0 else "#2ca02c"
            sign = "+" if chg >= 0 else ""
            cols[i].markdown(f"<div style='text-align:center;'><div>{name}</div><div style='font-size:1.8rem; font-weight:700;'>{value:.2f}</div><div style='color:{color};'>{sign}{chg:.2f}%</div></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 自选股
    with st.container():
        st.markdown('<div class="card"><h3 style="margin-top:0;">⭐ 自选股</h3>', unsafe_allow_html=True)
        available = [s for s in stocks if s not in st.session_state.watchlist]
        if available:
            add_stock = st.selectbox("添加股票", available, key="add_watch")
            if st.button("➕ 添加", key="add_btn"):
                st.session_state.watchlist.append(add_stock)
                st.rerun()
        else:
            st.info("所有股票已在自选股中")
        for stock in st.session_state.watchlist:
            price = get_price(latest_date, stock)
            prev_price = get_price(date_list[-2], stock)
            chg_pct = (price - prev_price) / prev_price * 100
            color = "#ff4d4d" if chg_pct >= 0 else "#2ca02c"
            sign = "+" if chg_pct >= 0 else ""
            c1, c2, c3, c4 = st.columns([2,1,1,1])
            c1.write(stock)
            c2.write(f"{price:.2f}")
            c3.markdown(f'<span style="color:{color};">{sign}{chg_pct:.2f}%</span>', unsafe_allow_html=True)
            if c4.button("买入", key=f"buy_{stock}"):
                st.session_state.quick_buy_stock = stock
                st.rerun()
        if st.session_state.watchlist:
            del_stock = st.selectbox("删除自选股", st.session_state.watchlist, key="del_watch")
            if st.button("🗑️ 删除", key="del_btn"):
                st.session_state.watchlist.remove(del_stock)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    # 交易卡片
    with st.container():
        st.markdown('<div class="card"><h3 style="margin-top:0;">💰 快捷交易</h3>', unsafe_allow_html=True)
        selected_date = st.date_input("交易日", value=start_date, min_value=start_date, max_value=end_date, key="trade_date")
        selected_date = pd.Timestamp(selected_date)
        stock_choice = st.selectbox("股票", stocks, index=stocks.index(st.session_state.quick_buy_stock) if st.session_state.quick_buy_stock in stocks else 0)
        action = st.radio("方向", ["买入", "卖出"], horizontal=True)
        qty = st.number_input("数量（股）", min_value=1, step=1, value=1)
        price = get_price(selected_date, stock_choice)
        st.markdown(f"<div style='text-align:center; margin:0.5rem 0;'><span style='font-size:1.8rem; font-weight:700; color:#FF8C42;'>{price:.2f}</span> 元</div>", unsafe_allow_html=True)
        if st.button("确认交易", use_container_width=True):
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

# 下方标签页
tab1, tab2, tab3 = st.tabs(["💼 我的持仓", "📈 资产曲线", "📜 交易明细"])
with tab1:
    holdings_list = []
    for s in stocks:
        q = st.session_state.holdings[s]
        if q > 0:
            p = get_price(latest_date, s)
            holdings_list.append({"股票": s, "持股数量": q, "最新价": f"{p:.2f}", "市值": f"{q*p:.2f}"})
    if holdings_list:
        st.dataframe(pd.DataFrame(holdings_list), use_container_width=True, hide_index=True)
    else:
        st.info("📭 暂无持仓，去买入一些股票吧")
with tab2:
    if st.session_state.transactions:
        history = [(start_date, 5000.0)]
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
        df_hist = pd.DataFrame(history, columns=["日期", "总资产"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_hist["日期"], y=df_hist["总资产"], mode="lines+markers", line=dict(color="#FF8C42", width=3)))
        fig.update_layout(title="总资产变化趋势", xaxis_title="日期", yaxis_title="总资产 (元)", plot_bgcolor="white", paper_bgcolor="white", font_color="#1e293b")
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

# 侧边栏结算
with st.sidebar:
    st.markdown("### 🎯 模拟结算")
    if st.button("结束模拟并计算最终收益"):
        final_total = get_total_asset(latest_date)
        profit = final_total - 5000
        rate = (profit / 5000) * 100
        st.success(f"✨ 总资产：{final_total:.2f} 元\n✨ 收益：{profit:+.2f} 元\n✨ 收益率：{rate:+.2f}%")
        st.balloons()
