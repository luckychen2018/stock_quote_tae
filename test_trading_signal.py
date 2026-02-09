#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试交易信号生成功能

这个脚本用于验证修改后的交易策略是否能正确生成买卖信号。
通过模拟股票价格的波动，包含上涨和下跌趋势，来测试交易信号的触发情况。
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from get_stock_quote import detect_signal, calculate_slope, determine_trend, DATA_WINDOW, SLOPE_THRESHOLD

# 重置全局变量
import get_stock_quote
get_stock_quote.highest_price = None


def simulate_trading():
    """
    模拟股票价格波动，测试交易信号生成
    """
    print("\n=== 开始测试交易信号生成功能 ===")
    print(f"参数配置：DATA_WINDOW={DATA_WINDOW}, SLOPE_THRESHOLD={SLOPE_THRESHOLD}")
    print(f"最小报价单位={get_stock_quote.MINIMUM_PRICE_UNIT}, 回撤阈值={get_stock_quote.RETURN_THRESHOLD_STEPS}步长")
    print("="*50)
    
    # 模拟股票价格序列（包含上涨、下跌和横盘）
    # 模拟黄金ETF价格波动
    simulated_prices = [
        9.04, 9.05, 9.06, 9.07, 9.06, 9.08, 9.09, 9.10, 9.11, 9.10,  # 小幅上涨
        9.09, 9.08, 9.07, 9.06, 9.05, 9.04, 9.03, 9.02, 9.01, 9.00,  # 下跌
        8.99, 8.98, 8.99, 9.00, 9.01, 9.02, 9.03, 9.04, 9.05, 9.06,  # 回升
        9.07, 9.08, 9.09, 9.10, 9.11, 9.12, 9.13, 9.14, 9.15, 9.16,  # 大幅上涨
        9.15, 9.14, 9.13, 9.12, 9.11, 9.10, 9.09, 9.08, 9.07, 9.06,  # 快速下跌
    ]
    
    # 模拟时间戳（间隔1秒）
    simulated_timestamps = list(range(len(simulated_prices)))
    
    # 历史数据存储
    history_prices = []
    history_timestamps = []
    
    # 趋势状态
    current_trend = "flat"
    previous_trend = "flat"
    
    # 交易统计
    buy_count = 0
    sell_count = 0
    hold_count = 0
    
    print("时间点 | 当前价格 | 前一价格 | 趋势变化 | 斜率 | 信号")
    print("-" * 70)
    
    # 模拟交易过程
    for i in range(len(simulated_prices)):
        current_price = simulated_prices[i]
        current_timestamp = simulated_timestamps[i]
        
        # 更新历史数据
        history_prices.append(current_price)
        history_timestamps.append(current_timestamp)
        
        # 保持窗口大小
        if len(history_prices) > DATA_WINDOW:
            history_prices.pop(0)
            history_timestamps.pop(0)
        
        # 计算趋势
        previous_trend = current_trend
        slope = 0
        if len(history_prices) >= 2:
            slope = calculate_slope(history_prices, history_timestamps)
            current_trend = determine_trend(slope)
        
        # 检测交易信号
        signal = "HOLD"
        if len(history_prices) >= 2:
            signal = detect_signal(current_price, history_prices[-2], current_trend, previous_trend)
        
        # 更新交易统计
        if signal == "BUY":
            buy_count += 1
        elif signal == "SELL":
            sell_count += 1
        else:
            hold_count += 1
        
        # 打印结果（只显示有信号的情况）
        if i > 0 and signal != "HOLD":
            print(f"{i:5d} | {current_price:8.3f} | {simulated_prices[i-1]:8.3f} | {previous_trend}->{current_trend} | {slope:7.4f} | {signal}")
    
    # 打印统计结果
    print("="*70)
    print(f"总时间点: {len(simulated_prices)}")
    print(f"买入信号: {buy_count}次")
    print(f"卖出信号: {sell_count}次")
    print(f"持有信号: {hold_count}次")
    print(f"交易总次数: {buy_count + sell_count}次")
    
    if buy_count + sell_count == 0:
        print("\n⚠️  警告：没有生成任何交易信号！")
        return False
    else:
        print("\n✅ 成功：生成了交易信号！")
        return True


if __name__ == "__main__":
    # 运行测试
    simulate_trading()
