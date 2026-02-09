import requests
import time
import math
from datetime import datetime
import statistics
import asciichartpy

# 新浪财经API URL
sina_stock_url = "http://hq.sinajs.cn/rn=%d&list=%s"

# 股票代码映射
market_map = {
    "sh": "上海",
    "sz": "深圳",
    "bj": "北京"
}

# 策略参数配置（可调整）
UPDATE_INTERVAL = 5  # 更新间隔，单位：秒
DATA_WINDOW = 5  # 计算趋势的窗口大小（最近5个数据点，减少平滑效果）
SLOPE_THRESHOLD = 0.001  # 斜率阈值，降低阈值使趋势更容易被检测到

# 基于最小报价单位的新参数配置
MINIMUM_PRICE_UNIT = 0.01  # 最小报价单位（黄金ETF通常为0.01元）
RETURN_THRESHOLD_STEPS = 2  # 回撤阈值的步长数，减少回撤要求

# 历史价格数据，用于计算趋势
history_prices = []
# 历史时间戳，用于计算时间差
history_timestamps = []
# 当前趋势状态（"up"上升, "down"下降, "flat"平坦）
current_trend = "flat"
# 最近一次的操作提示
last_signal = ""
# 最高价跟踪，用于计算回撤
highest_price = None

# 全量价格数据，用于显示完整走势图
full_history_prices = []
# 全量时间戳数据，用于记录起止时间
full_history_timestamps = []
# 监控开始时间
monitoring_start_time = None
# 监控结束时间
monitoring_end_time = None
# 监控轮次计数器
monitoring_round = 1

# 价格小数位数配置
price_decimal_places = 2  # 默认2位小数，将根据新浪接口数据动态调整

# 模拟交易参数
INITIAL_FUNDS = 10000.0  # 初始资金，单位：元
current_funds = INITIAL_FUNDS  # 当前资金
shares_held = 0  # 持有份额
initial_price = None  # 第一秒的基准价格
portfolio_value = INITIAL_FUNDS  # 总资产价值（资金+持仓市值）
trade_count = 0  # 交易次数

def get_stock_quote(stock_code):
    """
    获取指定股票代码的实时行情数据
    
    参数:
    stock_code: 股票代码，例如 "601919" (中远海控)
    
    返回:
    stock_info: 包含股票行情信息的字典
    """
    # 确定股票的市场前缀
    # 6开头和5开头的股票/ETF是上海市场，0开头的是深圳市场，8开头的是北京市场
    if stock_code.startswith("6") or stock_code.startswith("5"):
        full_code = f"sh{stock_code}"
    elif stock_code.startswith("0"):
        full_code = f"sz{stock_code}"
    elif stock_code.startswith("8"):
        full_code = f"bj{stock_code}"
    else:
        raise ValueError("无效的股票代码，请检查代码格式")
    
    # 生成请求URL
    rn = int(time.time())  # 时间戳，用于防止缓存
    url = sina_stock_url % (rn, full_code)
    
    # 设置请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Referer": "https://finance.sina.com.cn/"
    }
    
    # 发送请求
    try:
        response = requests.get(url, headers=headers)
        response.encoding = "gb18030"  # 新浪财经使用GB18030编码
        
        if response.status_code != 200:
            raise Exception(f"请求失败，状态码: {response.status_code}")
        
        # 解析响应内容
        data = response.text
        print(f"原始响应数据: {data}")
        
        # 解析数据
        stock_info = parse_stock_data(data, stock_code)
        # 如果解析失败，使用原始股票代码
        if stock_info and stock_info['股票代码'] != stock_code:
            print(f"解析出的股票代码与原始代码不一致，使用原始代码: {stock_code}")
            stock_info['股票代码'] = stock_code
        return stock_info
        
    except Exception as e:
        print(f"获取股票数据失败: {e}")
        return None

def parse_stock_data(data, original_stock_code=None):
    """
    解析新浪财经返回的股票数据
    
    参数:
    data: 新浪财经返回的原始数据字符串
    original_stock_code: 原始股票代码，用于解析失败时的回退
    
    返回:
    stock_info: 包含股票行情信息的字典
    """
    try:
        # 分割数据
        parts = data.split("=")
        if len(parts) < 2:
            raise Exception("无效的数据格式")
        
        # 获取股票代码
        code_part = parts[0]
        full_code = code_part.split("_")[1].strip()
        market = full_code[:2]
        stock_code = full_code[2:]
        
        # 获取股票数据
        data_part = parts[1].strip().strip('"')
        stock_data = data_part.split(",")
        
        if len(stock_data) < 32:
            raise Exception("数据不完整")
        
        # 获取原始价格字符串，分析小数位数
        current_price_str = stock_data[3]
        pre_close_str = stock_data[2]
        
        # 动态确定价格小数位数
        global price_decimal_places
        if '.' in current_price_str:
            price_decimal_places = len(current_price_str.split('.')[1])
        elif '.' in pre_close_str:
            price_decimal_places = len(pre_close_str.split('.')[1])
        else:
            price_decimal_places = 2  # 默认2位小数
        
        # 转换为浮点数
        current_price = float(current_price_str)
        pre_close = float(pre_close_str)
        
        # 计算涨跌幅和涨跌额（保持与原数据一致的小数位数）
        change_price = current_price - pre_close
        change_percent = (change_price / pre_close) * 100
        
        # 转换成交量和成交额为更易读的格式
        volume = int(stock_data[8]) // 100  # 转换为手
        amount = int(float(stock_data[9])) // 10000  # 转换为万元
        
        # 构建股票信息字典
        stock_info = {
            "股票代码": stock_code,
            "股票名称": stock_data[0],
            "今日开盘价": float(stock_data[1]),
            "昨日收盘价": pre_close,
            "当前价格": current_price,
            "今日最高价": float(stock_data[4]),
            "今日最低价": float(stock_data[5]),
            "竞买价": float(stock_data[6]),
            "竞卖价": float(stock_data[7]),
            "成交量": f"{volume}手",
            "成交额": f"{amount}万元",
            "买一申报": int(stock_data[10]) // 100,  # 转换为手
            "买一报价": float(stock_data[11]),
            "买二申报": int(stock_data[12]) // 100,  # 转换为手
            "买二报价": float(stock_data[13]),
            "买三申报": int(stock_data[14]) // 100,  # 转换为手
            "买三报价": float(stock_data[15]),
            "买四申报": int(stock_data[16]) // 100,  # 转换为手
            "买四报价": float(stock_data[17]),
            "买五申报": int(stock_data[18]) // 100,  # 转换为手
            "买五报价": float(stock_data[19]),
            "卖一申报": int(stock_data[20]) // 100,  # 转换为手
            "卖一报价": float(stock_data[21]),
            "卖二申报": int(stock_data[22]) // 100,  # 转换为手
            "卖二报价": float(stock_data[23]),
            "卖三申报": int(stock_data[24]) // 100,  # 转换为手
            "卖三报价": float(stock_data[25]),
            "卖四申报": int(stock_data[26]) // 100,  # 转换为手
            "卖四报价": float(stock_data[27]),
            "卖五申报": int(stock_data[28]) // 100,  # 转换为手
            "卖五报价": float(stock_data[29]),
            "日期": stock_data[30],
            "时间": stock_data[31],
            "市场": market_map.get(market, "未知"),
            "涨跌额": round(change_price, 2),
            "涨跌幅": f"{round(change_percent, 2)}%"
        }
        
        return stock_info
        
    except Exception as e:
        print(f"解析股票数据失败: {e}")
        return None

def print_stock_info(stock_info):
    """
    打印股票信息
    
    参数:
    stock_info: 包含股票行情信息的字典
    """
    if not stock_info:
        print("没有可显示的股票信息")
        return
    
    print("\n" + "="*50)
    print(f"股票代码: {stock_info['股票代码']} ({stock_info['股票名称']})")
    print(f"市场: {stock_info['市场']}")
    print(f"日期: {stock_info['日期']} 时间: {stock_info['时间']}")
    print("="*50)
    print(f"当前价格: {stock_info['当前价格']} 元")
    print(f"涨跌幅: {stock_info['涨跌幅']} 涨跌额: {stock_info['涨跌额']} 元")
    print("="*50)
    print(f"今日开盘价: {stock_info['今日开盘价']} 元")
    print(f"昨日收盘价: {stock_info['昨日收盘价']} 元")
    print(f"今日最高价: {stock_info['今日最高价']} 元")
    print(f"今日最低价: {stock_info['今日最低价']} 元")
    print("="*50)
    print(f"成交量: {stock_info['成交量']}")
    print(f"成交额: {stock_info['成交额']}")
    print("="*50)
    print("买卖盘:")
    print(f"买一: {stock_info['买一报价']} 元 {stock_info['买一申报']}手")
    print(f"买二: {stock_info['买二报价']} 元 {stock_info['买二申报']}手")
    print(f"买三: {stock_info['买三报价']} 元 {stock_info['买三申报']}手")
    print(f"买四: {stock_info['买四报价']} 元 {stock_info['买四申报']}手")
    print(f"买五: {stock_info['买五报价']} 元 {stock_info['买五申报']}手")
    print(f"卖一: {stock_info['卖一报价']} 元 {stock_info['卖一申报']}手")
    print(f"卖二: {stock_info['卖二报价']} 元 {stock_info['卖二申报']}手")
    print(f"卖三: {stock_info['卖三报价']} 元 {stock_info['卖三申报']}手")
    print(f"卖四: {stock_info['卖四报价']} 元 {stock_info['卖四申报']}手")
    print(f"卖五: {stock_info['卖五报价']} 元 {stock_info['卖五申报']}手")
    print("="*50)

def calculate_slope(prices, timestamps):
    """
    计算价格趋势的斜率
    
    参数:
    prices: 价格列表
    timestamps: 对应的时间戳列表
    
    返回:
    slope: 价格趋势的斜率
    """
    if len(prices) < 2:
        return 0
    
    # 计算时间差（转换为秒）
    time_diffs = [t - timestamps[0] for t in timestamps]
    
    # 使用线性回归计算斜率
    n = len(prices)
    sum_x = sum(time_diffs)
    sum_y = sum(prices)
    sum_xy = sum(x*y for x, y in zip(time_diffs, prices))
    sum_x2 = sum(x*x for x in time_diffs)
    
    if n*sum_x2 - sum_x*sum_x == 0:
        return 0
    
    slope = (n*sum_xy - sum_x*sum_y) / (n*sum_x2 - sum_x*sum_x)
    return slope

def determine_trend(slope):
    """
    根据斜率确定趋势方向
    
    参数:
    slope: 价格趋势的斜率
    
    返回:
    trend: 趋势方向 ("up"上升, "down"下降, "flat"平坦)
    """
    if abs(slope) < SLOPE_THRESHOLD:
        return "flat"
    elif slope > 0:
        return "up"
    else:
        return "down"

def detect_signal(current_price, previous_price, current_trend, previous_trend):
    """
    检测买卖信号，基于最小报价单位的涨跌阈值和回撤阈值
    
    参数:
    current_price: 当前价格
    previous_price: 前一个价格
    current_trend: 当前趋势
    previous_trend: 前一个趋势
    
    返回:
    signal: 买卖信号 ("BUY"买入, "SELL"卖出, "HOLD"持有)
    """
    global highest_price
    
    # 初始化最高价（确保在首次运行时能正确设置）
    if highest_price is None:
        highest_price = current_price
    # 更新最高价
    if current_price > highest_price:
        highest_price = current_price
    
    # 买入信号：增加多种买入条件，提高交易机会
    # 1. 趋势从下降转为上升
    # 2. 价格明显上涨且当前趋势为上升
    price_change = current_price - previous_price
    if (previous_trend == "down" and current_trend == "up") or \
       (current_trend == "up" and price_change > MINIMUM_PRICE_UNIT * 2):
        return "BUY"
    
    # 卖出信号：回撤达到设定的步长数或价格明显下跌
    if current_trend == "down":
        # 计算当前价格与最高价的差值
        price_diff = highest_price - current_price
        # 计算需要的回撤步长数
        required_diff = RETURN_THRESHOLD_STEPS * MINIMUM_PRICE_UNIT
        
        if price_diff >= required_diff:
            return "SELL"
    # 增加卖出条件：价格明显下跌
    elif current_price < previous_price - MINIMUM_PRICE_UNIT * 2:
        return "SELL"
    
    return "HOLD"

def record_data_to_file(stock_info, signal):
    """
    将详细的股票原始数据记录到文本文件，方便回测
    
    参数:
    stock_info: 股票行情信息字典
    signal: 买卖信号
    """
    # 确保文件保存在stock_quote文件夹中
    import os
    file_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(file_dir, f"stock_data_{stock_info['股票代码']}_{datetime.now().strftime('%Y%m%d')}.txt")
    
    with open(filename, "a", encoding="utf-8") as f:
        # 记录当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 写入数据 - 详细记录所有原始数据
        f.write(f"{current_time},"  # 时间戳
                f"{stock_info['股票代码']},"  # 股票代码
                f"{stock_info['股票名称']},"  # 股票名称
                f"{stock_info['今日开盘价']},"  # 今日开盘价
                f"{stock_info['昨日收盘价']},"  # 昨日收盘价
                f"{stock_info['当前价格']},"  # 当前价格
                f"{stock_info['今日最高价']},"  # 今日最高价
                f"{stock_info['今日最低价']},"  # 今日最低价
                f"{stock_info['竞买价']},"  # 竞买价
                f"{stock_info['竞卖价']},"  # 竞卖价
                f"{stock_info['成交量']},"  # 成交量(手)
                f"{stock_info['成交额']},"  # 成交额(万元)
                f"{stock_info['买一申报']},"  # 买一申报量(手)
                f"{stock_info['买一报价']},"  # 买一价格
                f"{stock_info['买二申报']},"  # 买二申报量(手)
                f"{stock_info['买二报价']},"  # 买二价格
                f"{stock_info['买三申报']},"  # 买三申报量(手)
                f"{stock_info['买三报价']},"  # 买三价格
                f"{stock_info['买四申报']},"  # 买四申报量(手)
                f"{stock_info['买四报价']},"  # 买四价格
                f"{stock_info['买五申报']},"  # 买五申报量(手)
                f"{stock_info['买五报价']},"  # 买五价格
                f"{stock_info['卖一申报']},"  # 卖一申报量(手)
                f"{stock_info['卖一报价']},"  # 卖一价格
                f"{stock_info['卖二申报']},"  # 卖二申报量(手)
                f"{stock_info['卖二报价']},"  # 卖二价格
                f"{stock_info['卖三申报']},"  # 卖三申报量(手)
                f"{stock_info['卖三报价']},"  # 卖三价格
                f"{stock_info['卖四申报']},"  # 卖四申报量(手)
                f"{stock_info['卖四报价']},"  # 卖四价格
                f"{stock_info['卖五申报']},"  # 卖五申报量(手)
                f"{stock_info['卖五报价']},"  # 卖五价格
                f"{stock_info['涨跌额']},"  # 涨跌额
                f"{stock_info['涨跌幅']},"  # 涨跌幅
                f"{signal}"  # 交易信号
                f"\n")
        
        # 如果是文件的第一行，写入表头
        if f.tell() == len(f"{current_time},{stock_info['股票代码']},{stock_info['股票名称']},{stock_info['今日开盘价']},{stock_info['昨日收盘价']},{stock_info['当前价格']},{stock_info['今日最高价']},{stock_info['今日最低价']},{stock_info['竞买价']},{stock_info['竞卖价']},{stock_info['成交量']},{stock_info['成交额']},{stock_info['买一申报']},{stock_info['买一报价']},{stock_info['买二申报']},{stock_info['买二报价']},{stock_info['买三申报']},{stock_info['买三报价']},{stock_info['买四申报']},{stock_info['买四报价']},{stock_info['买五申报']},{stock_info['买五报价']},{stock_info['卖一申报']},{stock_info['卖一报价']},{stock_info['卖二申报']},{stock_info['卖二报价']},{stock_info['卖三申报']},{stock_info['卖三报价']},{stock_info['卖四申报']},{stock_info['卖四报价']},{stock_info['卖五申报']},{stock_info['卖五报价']},{stock_info['涨跌额']},{stock_info['涨跌幅']},{signal}\n"):
            # 写入详细的表头
            f.seek(0)  # 回到文件开头
            header = "时间戳,股票代码,股票名称,今日开盘价,昨日收盘价,当前价格,今日最高价,今日最低价,竞买价,竞卖价,"
            header += "成交量(手),成交额(万元),买一申报(手),买一价格,买二申报(手),买二价格,买三申报(手),买三价格,"
            header += "买四申报(手),买四价格,买五申报(手),买五价格,卖一申报(手),卖一价格,卖二申报(手),卖二价格,"
            header += "卖三申报(手),卖三价格,卖四申报(手),卖四价格,卖五申报(手),卖五价格,涨跌额,涨跌幅,交易信号\n"
            f.write(header)

def print_strategy_explanation():
    """
    打印策略说明和科普内容
    """
    print("="*60)
    print("股票监控策略说明")
    print("="*60)
    print("策略原理：")
    print("1. 实时监控：每秒获取一次股票价格数据")
    print("2. 趋势分析：使用线性回归计算价格变化的斜率")
    print("3. 信号生成：")
    print("   - 当价格从下降趋势转为上升趋势时，立即发出买入信号")
    print("   - 当价格从最高价回撤达到指定步长时，发出卖出信号")
    print("4. 可视化：使用ASCII图表在终端显示价格随时间的变化")
    print()
    print("参数说明：")
    print(f"- 更新间隔：{UPDATE_INTERVAL}秒")
    print(f"- 趋势窗口：{DATA_WINDOW}个数据点")
    print(f"- 最小报价单位：{MINIMUM_PRICE_UNIT}元")
    print(f"- 回撤阈值步长：{RETURN_THRESHOLD_STEPS}个最小报价单位")
    print(f"- 斜率阈值：{SLOPE_THRESHOLD}")
    print()
    print("科普知识：")
    print("- 斜率：表示价格变化的速率，正数为上升，负数为下降")
    print("- 趋势窗口：用于计算趋势的数据点数量，窗口越大越平滑")
    print("- 最小报价单位：股票交易中允许的最小价格变动幅度")
    print("- 回撤阈值：价格从最高点下跌的幅度，用于触发卖出信号")
    print("- 实时监控：高频监控可以及时捕捉短期价格变化")
    print("- ASCII图表：使用字符在终端绘制的图表，适合简单的数据可视化")
    print("="*60)
    print()

def draw_price_chart(prices, chart_width=50, chart_height=10):
    """
    使用ASCII字符绘制价格变化趋势图
    
    参数:
    prices: 价格列表
    chart_width: 图表宽度（字符数）
    chart_height: 图表高度（字符数）
    """
    if not prices:
        return
    
    # 设置图表配置（动态小数位数）
    config = {
        'width': chart_width,
        'height': chart_height,
        'format': f'{{0:.{price_decimal_places}f}}',  # 与新浪接口返回的小数位数一致
        'offset': 3  # 标题空间
    }
    
    # 绘制图表
    print("\n价格走势图：")
    print("-" * (chart_width + 10))
    print(asciichartpy.plot(prices, config))
    print("-" * (chart_width + 10))
    # 动态小数位数格式化
    fmt_str = f'.{price_decimal_places}f'
    
    print(f"数据点数量: {len(prices)} 个 (每个点间隔 {UPDATE_INTERVAL} 秒)")
    print(f"价格范围: {min(prices):{fmt_str}} - {max(prices):{fmt_str}} 元")
    if len(prices) > 1:
        print(f"最高价: {max(prices):{fmt_str}}元，最低价: {min(prices):{fmt_str}}元")
        print(f"价格波动: {(max(prices) - min(prices)):{fmt_str}}元 ({((max(prices) - min(prices))/min(prices)*100):.2f}%)")
    print()

if __name__ == "__main__":
    # 简单测试功能
    print("测试股票行情获取功能...")
    stock_code = "518880"  # 华安黄金ETF
    stock_info = get_stock_quote(stock_code)
    if stock_info:
        print_stock_info(stock_info)
    else:
        print("获取股票数据失败")
    print("测试完成。")
    print("\n提示：在Web模式下，请运行 app.py 启动Web服务器。")
