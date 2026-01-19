# -*- coding: utf-8 -*-
import akshare as ak
import pandas as pd
import requests
import os

# ==========================================
# 🔧 配置区
# ==========================================
SENDKEY = os.getenv("SERVER_SENDKEY", "SCT309788ThhT0oEMhdmtjwXntJgFMRlvE")

BOARD_TO_ETF = {
    "人工智能": "515070", "AI": "515070", "算力": "516500",
    "芯片": "159995", "半导体": "159995",
    "光伏": "515790", "新能源": "516160",
    "证券": "512880", "券商": "512880",
    "白酒": "512690", "食品": "512690",
    "医药": "512010", "医疗": "159828",
    "军工": "512660", "国防": "512670",
    "有色金属": "512400", "黄金": "518800",
    "煤炭": "515220", "钢铁": "512400",
    "default": "515070"
}

def send_msg(title, content):
    url = f"https://sctapi.ftqq.com/{SENDKEY}.send"
    data = {"title": title, "desp": content}
    try:
        requests.post(url, data=data, timeout=10)
        print("✅ 推送成功")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

def get_hot_boards():
    try:
        df = ak.stock_board_concept_name_em()
        boards = df['板块名称'].head(3).tolist()
        print(f"🔥 获取热门板块: {boards}")
        return boards
    except Exception as e:
        print(f"板块获取失败: {e}")
        return ["人工智能", "芯片", "光伏"]

def get_etf_code(board_name):
    for keyword, code in BOARD_TO_ETF.items():
        if keyword in board_name:
            return code
    return BOARD_TO_ETF["default"]

def check_etf_trend(symbol):
    try:
        df = ak.fund_etf_hist_em(symbol=symbol)
        if df.empty or len(df) < 10:
            return False, "数据不足"
        df['ma5'] = df['收盘'].rolling(5).mean()
        df['ma10'] = df['收盘'].rolling(10).mean()
        latest = df.iloc[-1]
        if latest['收盘'] > latest['ma5'] > latest['ma10']:
            return True, "ETF多头 (主力进场)"
        else:
            return False, "ETF空头 (主力观望)"
    except:
        return False, "ETF分析异常"

def check_stock_chip(symbol):
    try:
        df = ak.stock_zh_a_hist(symbol=symbol, adjust="qfq")
        if df.empty or len(df) < 20:
            return None
        # 计算筹码集中度
        turnover_std = df['成交量'].tail(10).std() / df['成交量'].tail(10).mean()
        pct_change = (df['收盘'].iloc[-1] - df['收盘'].iloc[-10]) / df['收盘'].iloc[-10]
        # 主力锁仓逻辑
        if turnover_std < 0.3 and pct_change < 0.15:
            return {
                "symbol": symbol,
                "name": df.iloc[-1]['名称'],
                "score": "🔴 强",
                "reason": f"主力锁仓"
            }
        else:
            return None
    except Exception as e:
        return None

def main():
    print("🚀 查主力监控系统 V3.1 启动")
    final_results = []
    hot_boards = get_hot_boards()
    
    for board in hot_boards:
        print(f"\n🔍 分析板块: {board}")
        etf_symbol = get_etf_code(board)
        print(f"   📈 关联ETF: {etf_symbol}")
        etf_ok, etf_msg = check_etf_trend(etf_symbol)
        if not etf_ok:
            print(f"   🚫 跳过: {etf_msg}")
            continue
        try:
            df_stocks = ak.stock_board_concept_cons_em(symbol=board)
            top_stocks = df_stocks[['代码', '名称']].head(10).to_dict('records')
        except:
            top_stocks = [{"代码": "600000", "名称": "浦发银行"}]
        
        hit_stocks = []
        for stock in top_stocks:
            symbol = stock['代码']
            if not (symbol.startswith('6') or symbol.startswith('0') or symbol.startswith('3')):
                continue
            result = check_stock_chip(symbol)
            if result:
                result['etf_symbol'] = etf_symbol
                result['etf_msg'] = etf_msg
                hit_stocks.append(result)
        
        if hit_stocks:
            final_results.append({
                "board": board,
                "etf": etf_symbol,
                "stocks": hit_stocks
            })
    
    if final_results:
        content = "🚀🚀 **【主力掘金日报 - ETF共振版】** 🚀🚀\n\n"
        content += "*(仅展示板块与个股共振信号)*\n\n"
        for item in final_results:
            content += f"🔥 **板块: {item['board']} | ETF: {item['etf']}**\n"
            for stock in item['stocks']:
                content += f"- {stock['symbol']} {stock['name']} ({stock['score']})\n"
            content += "---\n"
        content += f"\n📅 *数据时间: {pd.Timestamp.now().strftime('%m-%d %H:%M')}*"
        send_msg("【明日策略】主力资金已就位", content)
    else:
        send_msg("【主力监控】日常报告", "🔍 今日全市场扫描完毕，暂未发现主力资金共振信号，请耐心等待。")

if __name__ == "__main__":
    main()
