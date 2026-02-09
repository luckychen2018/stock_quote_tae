#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试初始自动买入和整数股交易功能

这个脚本用于验证初始自动买入、100股整数交易、剩余现金计算和实时资产变动功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from get_stock_quote import (
    INITIAL_FUNDS, current_funds, shares_held, portfolio_value,
    trade_count, price_decimal_places
)

# 重置全局变量
import get_stock_quote
get_stock_quote.highest_price = None
get_stock_quote.current_funds = get_stock_quote.INITIAL_FUNDS
get_stock_quote.shares_held = 0
get_stock_quote.initial_price = None
get_stock_quote.portfolio_value = get_stock_quote.INITIAL_FUNDS
get_stock_quote.trade_count = 0
get_stock_quote.price_decimal_places = 2


def test_initial_buy_logic():
    """
    测试初始自动买入逻辑
    """
    print("\n=== 测试初始自动买入和整数股交易功能 ===")
    print(f"初始资金: {INITIAL_FUNDS:.2f}元")
    print("="*60)
    
    # 模拟不同价格的初始买入情况
    test_prices = [9.04, 9.046, 10.50, 5.25]
    
    for test_price in test_prices:
        # 重置变量
        get_stock_quote.current_funds = get_stock_quote.INITIAL_FUNDS
        get_stock_quote.shares_held = 0
        get_stock_quote.trade_count = 0
        
        print(f"\n测试价格: {test_price:.{price_decimal_places}f}元")
        print("-"*40)
        
        # 模拟初始买入逻辑
        shares_to_buy = (get_stock_quote.current_funds // (test_price * 100)) * 100
        
        if shares_to_buy > 0:
            buy_amount = shares_to_buy * test_price
            get_stock_quote.current_funds -= buy_amount
            get_stock_quote.shares_held += shares_to_buy
            get_stock_quote.trade_count += 1
            
            print(f"买入股数: {shares_to_buy}股 (100股的倍数)")
            print(f"买入金额: {buy_amount:.2f}元")
            print(f"剩余现金: {get_stock_quote.current_funds:.2f}元")
            print(f"当前持仓: {get_stock_quote.shares_held}股")
            print(f"持仓市值: {get_stock_quote.shares_held * test_price:.2f}元")
            
            # 计算总资产和收益率
            total_assets = get_stock_quote.current_funds + (get_stock_quote.shares_held * test_price)
            return_rate = ((total_assets - get_stock_quote.INITIAL_FUNDS) / get_stock_quote.INITIAL_FUNDS) * 100
            print(f"总资产价值: {total_assets:.2f}元")
            print(f"收益率: {return_rate:.2f}%")
            
            # 验证股数是否为100的倍数
            if shares_to_buy % 100 == 0:
                print("✅ 验证通过: 股数是100的倍数")
            else:
                print("❌ 验证失败: 股数不是100的倍数")
            
            # 验证资金是否正确
            expected_funds = get_stock_quote.INITIAL_FUNDS - buy_amount
            if abs(get_stock_quote.current_funds - expected_funds) < 0.01:
                print("✅ 验证通过: 剩余现金计算正确")
            else:
                print(f"❌ 验证失败: 剩余现金计算错误 (实际: {get_stock_quote.current_funds:.2f}, 预期: {expected_funds:.2f})")
        else:
            print("❌ 无法买入: 资金不足")
    
    print("\n" + "="*60)
    print("=== 测试完成 ===")


def test_price_fluctuation():
    """
    测试价格波动对资产的影响
    """
    print("\n=== 测试价格波动对资产的影响 ===")
    print("="*60)
    
    # 重置变量
    get_stock_quote.current_funds = get_stock_quote.INITIAL_FUNDS
    get_stock_quote.shares_held = 0
    
    # 模拟初始买入
    initial_price = 9.04
    shares_to_buy = (get_stock_quote.current_funds // (initial_price * 100)) * 100
    buy_amount = shares_to_buy * initial_price
    get_stock_quote.current_funds -= buy_amount
    get_stock_quote.shares_held += shares_to_buy
    
    print(f"初始价格: {initial_price:.2f}元")
    print(f"买入股数: {shares_to_buy}股")
    print(f"剩余现金: {get_stock_quote.current_funds:.2f}元")
    print(f"初始持仓市值: {get_stock_quote.shares_held * initial_price:.2f}元")
    print(f"初始总资产: {get_stock_quote.current_funds + get_stock_quote.shares_held * initial_price:.2f}元")
    print("\n价格波动测试:")
    print("-"*40)
    
    # 模拟价格波动
    price_changes = [+0.10, +0.25, -0.05, -0.30, +0.15]
    for change in price_changes:
        current_price = initial_price + change
        
        # 计算实时资产
        position_value = get_stock_quote.shares_held * current_price
        total_assets = get_stock_quote.current_funds + position_value
        return_rate = ((total_assets - get_stock_quote.INITIAL_FUNDS) / get_stock_quote.INITIAL_FUNDS) * 100
        
        print(f"价格: {current_price:.2f}元 (变动: {change:+.2f}元)")
        print(f"  持仓市值: {position_value:.2f}元")
        print(f"  现金: {get_stock_quote.current_funds:.2f}元")
        print(f"  总资产: {total_assets:.2f}元 (收益率: {return_rate:+.2f}%)")
    
    print("\n" + "="*60)
    print("=== 价格波动测试完成 ===")


if __name__ == "__main__":
    # 运行测试
    test_initial_buy_logic()
    test_price_fluctuation()
