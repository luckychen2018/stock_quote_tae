# -*- coding: utf-8 -*-
"""
新增功能演示脚本
展示监控轮次、起止时间和全量价格走势图功能
"""
import time
import asciichartpy

# 模拟股票价格数据生成
def generate_stock_prices(start_price=2.0, num_points=100, volatility=0.01):
    """生成模拟的股票价格数据"""
    import random
    prices = [start_price]
    timestamps = [time.time()]
    
    for i in range(1, num_points):
        change = random.uniform(-volatility, volatility) * prices[-1]
        new_price = max(0.01, prices[-1] + change)
        prices.append(new_price)
        timestamps.append(time.time() + i)
    
    return prices, timestamps

# 模拟监控轮次、起止时间和价格数据
def simulate_monitoring_session():
    print("=== 模拟监控会话 ===")
    
    # 模拟第1轮监控
    round_num = 1
    start_time = time.time()
    
    # 生成模拟价格数据
    prices, timestamps = generate_stock_prices(num_points=50)
    
    # 模拟监控持续时间
    time.sleep(0.1)  # 模拟监控过程
    
    end_time = time.time()
    duration = end_time - start_time
    
    # 显示监控信息
    print(f"\n\033[1;33m=== 模拟交易最终结果 ===\033[0m")
    print(f"监控轮次: 第 {round_num} 轮")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    print(f"结束时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    print(f"监控时长: {int(duration // 60)}分{int(duration % 60)}秒")
    print(f"初始资金: 10000.00元")
    print(f"当前资金: 10150.75元")
    print(f"持有份额: 850.0000份")
    print(f"持仓市值: 1742.50元")
    print(f"总资产价值: 11893.25元")
    print(f"总收益率: 18.9325%")
    print(f"交易总次数: 4次")
    
    # 显示全量价格走势图
    print(f"\n\033[1;36m=== 全量价格走势图 (共 {len(prices)} 个数据点) ===\033[0m")
    draw_price_chart(prices)
    
    # 模拟第2轮监控
    round_num += 1
    print(f"\n\n=== 第 {round_num} 轮监控开始 ===")
    start_time = end_time + 300  # 5分钟后开始新一轮监控
    end_time = start_time + 180  # 监控3分钟
    
    # 显示监控信息
    duration = end_time - start_time
    print(f"\n\033[1;33m=== 模拟交易最终结果 ===\033[0m")
    print(f"监控轮次: 第 {round_num} 轮")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    print(f"结束时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    print(f"监控时长: {int(duration // 60)}分{int(duration % 60)}秒")
    print(f"初始资金: 11893.25元")
    print(f"当前资金: 12560.30元")
    print(f"持有份额: 1200.0000份")
    print(f"持仓市值: 2472.00元")
    print(f"总资产价值: 15032.30元")
    print(f"总收益率: 50.3230%")
    print(f"交易总次数: 7次")

# 绘制价格走势图
def draw_price_chart(prices, chart_width=70, chart_height=15):
    """
    使用ASCII字符绘制价格变化趋势图
    """
    if not prices:
        return
    
    # 设置图表配置
    config = {
        'width': chart_width,
        'height': chart_height,
        'format': '{0:.2f}',  # 与实时价格一致，使用2位小数
        'offset': 3
    }
    
    # 绘制图表
    print("\n价格走势图：")
    print("-" * (chart_width + 10))
    print(asciichartpy.plot(prices, config))
    print("-" * (chart_width + 10))
    print(f"数据点数量: {len(prices)} 个")
    print(f"价格范围: {min(prices):.2f} - {max(prices):.2f} 元")
    print(f"最高价: {max(prices):.2f}元，最低价: {min(prices):.2f}元")
    print(f"价格波动: {(max(prices) - min(prices)):.2f}元 ({((max(prices) - min(prices))/min(prices)*100):.2f}%)")
    print()

# 主程序
if __name__ == "__main__":
    print("========== 交易策略新增功能演示 ==========\n")
    
    # 功能说明
    print("1. 新增监控维度：")
    print("   - 监控轮次：自动记录监控会话的轮次")
    print("   - 起止时间：显示监控开始和结束的具体时间")
    print("   - 监控时长：计算并显示监控持续的分钟和秒数")
    print("\n2. 全量价格走势图：")
    print("   - 记录所有价格数据点")
    print("   - 显示完整的价格变化趋势")
    print("   - 提供价格范围、最高价、最低价和波动百分比")
    print("\n3. 增强的交易结果显示：")
    print("   - 包含轮次信息")
    print("   - 详细的时间统计")
    print("   - 完整的价格走势可视化")
    
    print("\n" + "="*50)
    
    # 模拟监控会话
    simulate_monitoring_session()
    
    print("\n========== 功能演示结束 ==========")
    print("\n使用方法：")
    print("1. 运行 get_stock_quote.py 开始监控")
    print("2. 按 Ctrl+C 停止监控")
    print("3. 查看包含新增功能的完整监控结果")
