import time
import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入我们的模块
from stock_quote.get_stock_quote import (
    draw_price_chart, monitoring_start_time, monitoring_end_time, 
    full_history_prices, full_history_timestamps, monitoring_round
)

# 模拟生成一些价格数据
def generate_test_prices(start_price=2.0, num_points=20, volatility=0.01):
    """生成模拟的价格数据"""
    import random
    prices = [start_price]
    for i in range(1, num_points):
        change = random.uniform(-volatility, volatility) * prices[-1]
        new_price = max(0.01, prices[-1] + change)
        prices.append(new_price)
    return prices

# 测试新增功能
def test_new_features():
    print("=== 测试新增功能 ===\n")
    
    # 1. 测试监控轮次功能
    print(f"监控轮次: {monitoring_round}")
    
    # 2. 测试时间记录功能
    print(f"监控开始时间: {monitoring_start_time}")
    print(f"监控结束时间: {monitoring_end_time}")
    
    # 3. 测试全量价格走势图
    test_prices = generate_test_prices(num_points=50)
    print(f"\n生成 {len(test_prices)} 个模拟价格数据点")
    
    # 更新全量价格数据
    global full_history_prices, full_history_timestamps
    full_history_prices = test_prices
    full_history_timestamps = [time.time() - (len(test_prices) - i) for i in range(len(test_prices))]
    
    # 绘制全量价格走势图
    print("\n=== 绘制全量价格走势图 ===")
    draw_price_chart(full_history_prices, chart_width=60, chart_height=10)
    
    # 4. 测试监控时长计算
    if monitoring_start_time and monitoring_end_time:
        duration = monitoring_end_time - monitoring_start_time
        print(f"监控时长: {int(duration // 60)}分{int(duration % 60)}秒")
    
    print("\n=== 测试完成 ===")

# 测试模拟交易结果显示
def test_trade_result_display():
    print("\n=== 测试模拟交易结果显示 ===")
    
    # 模拟交易结果数据
    INITIAL_FUNDS = 10000.0
    current_funds = 10230.50
    shares_held = 1500.0000
    current_price = 2.05
    trade_count = 3
    
    # 计算总资产
    portfolio_value = current_funds + shares_held * current_price
    
    # 模拟起止时间
    start_time = time.time() - 3600  # 1小时前
    end_time = time.time()
    duration = end_time - start_time
    
    # 显示模拟结果
    print(f"\n\033[1;33m=== 模拟交易最终结果 ===\033[0m")
    print(f"监控轮次: 第 {monitoring_round} 轮")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    print(f"结束时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    print(f"监控时长: {int(duration // 60)}分{int(duration % 60)}秒")
    print(f"初始资金: {INITIAL_FUNDS:.2f}元")
    print(f"当前资金: {current_funds:.2f}元")
    print(f"持有份额: {shares_held:.4f}份")
    print(f"持仓市值: {(shares_held * current_price):.2f}元")
    print(f"总资产价值: {portfolio_value:.2f}元")
    print(f"总收益率: {((portfolio_value - INITIAL_FUNDS) / INITIAL_FUNDS * 100):.4f}%")
    print(f"交易总次数: {trade_count}次")

if __name__ == "__main__":
    test_new_features()
    test_trade_result_display()
