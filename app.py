import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# ========== 页面配置 ==========
st.set_page_config(page_title="实时模拟炒股系统", layout="wide")
st.title("📊 实时模拟炒股系统")
st.markdown("**初始资金：5000元 | 实时股价（真实数据）**")

# ========== 初始化状态 ==========
if "cash" not in st.session_state:
    st.session_state.cash = 5000.0
if "holdings" not in st.session_state:
    st.session_state.holdings = {"招商银行": 0, "贵州茅台": 0, "宁德时代": 0}
if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "total_value_history" not in st.session_state:
    st.session_state.total_value_history = []

# ========== 股票代码映射（A股）==========
SYMBOL_MAP = {
    "招商银行": "600036.SS",
    "贵州茅台": "600519.SS",
    "宁德时代": "300750.SZ"
}
stocks = list(SYMBOL_MAP.keys())

# ========== 获取实时股价（带缓存，每5分钟刷新）==========
@st.cache_data(ttl=300)
def get_realtime_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")
        if not data.empty:
            return round(data['Close'].iloc[-1], 2)
        return None
    except:
        return None

# 获取所有股票实时价格
prices = {}
for stock in stocks:
    sym = SYMBOL_MAP[stock]
    price = get_realtime_price(sym)
    if price is None:
        # 如果获取失败，显示提示但继续（部署环境通常正常）
        price = 0.0
    prices[stock] = price

# ========== 显示实时股价卡片 ==========
st.sidebar.header("📈 实时行情")
col1, col2, col3 = st.sidebar.columns(3)
with col1:
    st.metric("招商银行", f"{prices['招商银行']:.2f}" if prices['招商银行'] else "获取中")
with col2:
    st.metric("贵州茅台", f"{prices['贵州茅台']:.2f}" if prices['贵州茅台'] else "获取中")
with col3:
    st.metric("宁德时代", f"{prices['宁德时代']:.2f}" if prices['宁德时代'] else "获取中")

st.sidebar.markdown("---")
st.sidebar.info("数据来源：Yahoo Finance (实时)")

# ========== 交易操作区 ==========
st.header("💰 交易操作")
colA, colB, colC = st.columns(3)
with colA:
    stock_choice = st.selectbox("选择股票", stocks)
with colB:
    action = st.radio("操作", ["买入", "卖出"], horizontal=True)
with colC:
    qty = st.number_input("数量（股）", min_value=1, step=1, value=100)

# 显示当前股价
current_price = prices[stock_choice]
if current_price > 0:
    st.info(f"当前 {stock_choice} 实时价格：**{current_price:.2f} 元**")
else:
    st.error("暂时无法获取股价，请检查网络或稍后重试")

# 执行交易
if st.button("✅ 确认交易", use_container_width=True):
    if current_price <= 0:
        st.error("无法获取股价，交易取消")
    else:
        total_cost = current_price * qty
        if action == "买入":
            if total_cost <= st.session_state.cash:
                st.session_state.cash -= total_cost
                st.session_state.holdings[stock_choice] += qty
                st.session_state.transactions.append({
                    "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "股票": stock_choice,
                    "操作": "买入",
                    "数量": qty,
                    "价格": current_price,
                    "金额": total_cost
                })
                st.success(f"✅ 成功买入 {qty} 股 {stock_choice}，花费 {total_cost:.2f} 元")
            else:
                st.error(f"❌ 现金不足！需要 {total_cost:.2f} 元，当前现金 {st.session_state.cash:.2f} 元")
        else:  # 卖出
            if qty <= st.session_state.holdings[stock_choice]:
                st.session_state.cash += total_cost
                st.session_state.holdings[stock_choice] -= qty
                st.session_state.transactions.append({
                    "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "股票": stock_choice,
                    "操作": "卖出",
                    "数量": qty,
                    "价格": current_price,
                    "金额": total_cost
                })
                st.success(f"✅ 成功卖出 {qty} 股 {stock_choice}，获得 {total_cost:.2f} 元")
            else:
                st.error(f"❌ 持股不足！你只有 {st.session_state.holdings[stock_choice]} 股 {stock_choice}")

# ========== 资产状况 ==========
st.subheader("💵 当前资产状况")
cash_col, value_col = st.columns(2)
with cash_col:
    st.metric("现金余额", f"{st.session_state.cash:.2f} 元")
with value_col:
    # 计算持仓总市值
    total_market_value = 0
    holdings_data = []
    for stock, qty in st.session_state.holdings.items():
        if qty > 0:
            price = prices[stock]
            if price > 0:
                market_value = qty * price
                total_market_value += market_value
                holdings_data.append({
                    "股票": stock,
                    "持股数量": qty,
                    "最新价": price,
                    "市值": round(market_value, 2)
                })
    total_asset = st.session_state.cash + total_market_value
    st.metric("总资产", f"{total_asset:.2f} 元", delta=round(total_asset-5000, 2))

if holdings_data:
    st.table(pd.DataFrame(holdings_data))
else:
    st.info("暂无持仓")

# ========== 交易记录表 ==========
st.subheader("📜 交易明细")
if st.session_state.transactions:
    trans_df = pd.DataFrame(st.session_state.transactions)
    st.dataframe(trans_df, use_container_width=True)
else:
    st.info("暂无交易记录")

# ========== 总资产变化曲线（记录每次交易后的资产）==========
# 每次交易后自动记录总资产
def record_asset():
    total_mv = 0
    for stock, qty in st.session_state.holdings.items():
        price = prices.get(stock, 0)
        if price and qty > 0:
            total_mv += qty * price
    total = st.session_state.cash + total_mv
    st.session_state.total_value_history.append((datetime.now(), total))

# 如果有新交易，记录（这里简单地在每次页面刷新时记录，避免重复）
# 为了曲线好看，每次交易后调用record_asset，但需要在交易代码中加入。上面交易代码可加，为简洁，我们在展示曲线前强制记录一次当前总资产。
if st.session_state.transactions:
    # 记录最后一次交易后的资产
    total_mv = 0
    for stock, qty in st.session_state.holdings.items():
        price = prices.get(stock, 0)
        if price and qty > 0:
            total_mv += qty * price
    total = st.session_state.cash + total_mv
    if not st.session_state.total_value_history or st.session_state.total_value_history[-1][1] != total:
        st.session_state.total_value_history.append((datetime.now(), total))

st.subheader("📈 总资产变化曲线")
if len(st.session_state.total_value_history) >= 2:
    hist_df = pd.DataFrame(st.session_state.total_value_history, columns=["时间", "总资产"])
    hist_df = hist_df.set_index("时间")
    st.line_chart(hist_df)
else:
    st.info("完成一笔交易后，资产曲线会显示在这里")

# ========== 最终结算按钮 ==========
st.sidebar.markdown("---")
if st.sidebar.button("🎯 结束模拟并计算收益"):
    total_mv_final = 0
    for stock, qty in st.session_state.holdings.items():
        price = prices.get(stock, 0)
        if price and qty > 0:
            total_mv_final += qty * price
    final_total = st.session_state.cash + total_mv_final
    profit = final_total - 5000
    profit_rate = (profit / 5000) * 100
    st.sidebar.success(f"### 最终结算")
    st.sidebar.write(f"**总资产：{final_total:.2f} 元**")
    st.sidebar.write(f"**收益：{profit:+.2f} 元**")
    st.sidebar.write(f"**收益率：{profit_rate:+.2f}%**")
    st.balloons()
