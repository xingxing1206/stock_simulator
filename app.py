import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 页面配置
st.set_page_config(page_title="专业炒股模拟器", layout="wide")
st.sidebar.title("📌 导航菜单")
page = st.sidebar.radio("选择页面", ["📈 交易", "💼 持仓", "📜 交易记录", "📊 结算与曲线"])

# 初始化数据
if "cash" not in st.session_state:
    st.session_state.cash = 5000.0
if "holdings" not in st.session_state:
    st.session_state.holdings = {"招商银行": 0, "贵州茅台": 0, "宁德时代": 0}
if "transactions" not in st.session_state:
    st.session_state.transactions = []

# 生成日期范围 2026-04-10 至 2026-05-29
start_date = datetime(2026, 4, 10)
end_date = datetime(2026, 5, 29)
date_list = []
current = start_date
while current <= end_date:
    date_list.append(current)
    current += timedelta(days=1)

# 生成模拟股价（固定随机种子，保证每次运行一致，看起来像真实历史数据）
np.random.seed(42)
stocks = ["招商银行", "贵州茅台", "宁德时代"]
base_prices = {"招商银行": 35.0, "贵州茅台": 1650.0, "宁德时代": 180.0}
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

def record_transaction(date, stock, action, qty, price, amount):
    st.session_state.transactions.append({
        "日期": date.strftime("%Y-%m-%d"),
        "股票": stock,
        "操作": action,
        "数量": qty,
        "价格": round(price, 2),
        "金额": round(amount, 2)
    })

# 页面1：交易
if page == "📈 交易":
    st.title("📈 模拟交易")
    st.markdown(f"**初始资金：5000元 | 交易时间：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}**")
    
    selected_date = st.date_input("选择交易日", value=start_date, min_value=start_date, max_value=end_date)
    selected_date = pd.Timestamp(selected_date)
    
    st.subheader(f"📊 {selected_date.strftime('%Y-%m-%d')} 股价")
    cols = st.columns(3)
    for i, stock in enumerate(stocks):
        price = get_price(selected_date, stock)
        cols[i].metric(stock, f"{price:.2f} 元")
    
    with st.form("trade_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            stock_choice = st.selectbox("股票", stocks)
        with col2:
            action = st.radio("操作", ["买入", "卖出"], horizontal=True)
        with col3:
            qty = st.number_input("数量（股）", min_value=1, step=100, value=100)
        submitted = st.form_submit_button("确认交易", use_container_width=True)
        
        if submitted:
            price = get_price(selected_date, stock_choice)
            total_cost = price * qty
            if action == "买入":
                if total_cost <= st.session_state.cash:
                    st.session_state.cash -= total_cost
                    st.session_state.holdings[stock_choice] += qty
                    record_transaction(selected_date, stock_choice, "买入", qty, price, total_cost)
                    st.success(f"✅ 成功买入 {qty} 股 {stock_choice}，花费 {total_cost:.2f} 元")
                else:
                    st.error(f"❌ 现金不足！需要 {total_cost:.2f} 元，当前现金 {st.session_state.cash:.2f} 元")
            else:
                if qty <= st.session_state.holdings[stock_choice]:
                    st.session_state.cash += total_cost
                    st.session_state.holdings[stock_choice] -= qty
                    record_transaction(selected_date, stock_choice, "卖出", qty, price, total_cost)
                    st.success(f"✅ 成功卖出 {qty} 股 {stock_choice}，获得 {total_cost:.2f} 元")
                else:
                    st.error(f"❌ 持股不足！你只有 {st.session_state.holdings[stock_choice]} 股 {stock_choice}")
    
    st.sidebar.metric("当前现金", f"{st.session_state.cash:.2f} 元")

# 页面2：持仓
elif page == "💼 持仓":
    st.title("💼 我的持仓")
    holdings_list = []
    total_market_value = 0
    latest_date = end_date
    for stock in stocks:
        qty = st.session_state.holdings[stock]
        if qty > 0:
            price = get_price(latest_date, stock)
            market_value = qty * price
            total_market_value += market_value
            holdings_list.append({
                "股票": stock,
                "持股数量": qty,
                "最新价": round(price, 2),
                "市值": round(market_value, 2)
            })
    if holdings_list:
        st.dataframe(pd.DataFrame(holdings_list), use_container_width=True)
        st.metric("持仓总市值", f"{total_market_value:.2f} 元")
        st.metric("总资产", f"{st.session_state.cash + total_market_value:.2f} 元")
    else:
        st.info("暂无持仓，请先去「交易」页面买入股票。")

# 页面3：交易记录
elif page == "📜 交易记录":
    st.title("📜 交易明细")
    if st.session_state.transactions:
        df_trans = pd.DataFrame(st.session_state.transactions)
        st.dataframe(df_trans, use_container_width=True)
        csv = df_trans.to_csv(index=False).encode('utf-8')
        st.download_button("导出交易记录为CSV", csv, "transactions.csv", "text/csv")
    else:
        st.info("暂无交易记录，请先去「交易」页面进行买卖。")

# 页面4：结算与曲线
elif page == "📊 结算与曲线":
    st.title("📊 最终结算 & 资产曲线")
    
    final_date = end_date
    final_cash = st.session_state.cash
    final_stock_value = sum(st.session_state.holdings[s] * get_price(final_date, s) for s in stocks)
    final_total = final_cash + final_stock_value
    profit = final_total - 5000
    profit_rate = (profit / 5000) * 100
    
    col1, col2, col3 = st.columns(3)
    col1.metric("总资产", f"{final_total:.2f} 元", delta=f"{profit:+.2f}")
    col2.metric("收益", f"{profit:+.2f} 元")
    col3.metric("收益率", f"{profit_rate:+.2f}%")
    
    # 绘制资产变化曲线
    if st.session_state.transactions:
        history = [(start_date, 5000.0)]
        cash_temp = 5000.0
        holdings_temp = {s: 0 for s in stocks}
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
            stock_value = sum(holdings_temp[s] * get_price(date, s) for s in stocks)
            total = cash_temp + stock_value
            history.append((date, total))
        hist_df = pd.DataFrame(history, columns=["日期", "总资产"]).drop_duplicates("日期", keep="last").set_index("日期")
        st.subheader("总资产变化曲线")
        st.line_chart(hist_df)
    else:
        st.info("暂无交易记录，无法绘制曲线。请先进行交易。")
    
    if st.button("🎯 结束模拟并计算最终收益", use_container_width=True):
        st.balloons()
        st.success(f"模拟结束！最终总资产：{final_total:.2f} 元，收益：{profit:+.2f} 元，收益率：{profit_rate:+.2f}%")
