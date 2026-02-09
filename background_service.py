import time
import threading
import os
from datetime import datetime, date
import get_stock_quote
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 创建数据库引擎
engine = create_engine('sqlite:///stock_data.db', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# 导入数据模型
from app import Watchlist, StockQuote

# 后台服务运行状态
running = False

# 数据获取间隔（秒）
FETCH_INTERVAL = 300  # 5分钟

# 锁文件路径
LOCK_FILE = 'background_service.lock'

# 检查并创建锁文件，确保只有一个实例在运行
def check_lock_file():
    # 检查锁文件是否存在
    if os.path.exists(LOCK_FILE):
        # 尝试读取锁文件中的进程ID
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = f.read().strip()
            # 检查进程是否存在
            if os.name == 'nt':  # Windows系统
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(1, 0, int(pid))
                if handle != 0:
                    kernel32.CloseHandle(handle)
                    print(f"后台服务已经在运行（进程ID: {pid}），退出当前实例")
                    return False
        except:
            pass
    # 创建或更新锁文件，写入当前进程ID
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
    return True

# 检查是否在交易时间内
def is_trading_time():
    # 获取当前时间
    now = datetime.now()
    current_time = now.time()
    current_date = now.date()
    
    # 检查是否是工作日（周一到周五）
    if current_date.weekday() >= 5:  # 0-4是周一到周五，5-6是周六和周日
        return False
    
    # 检查是否在交易时间内
    # 上午交易时间：9:30-11:30
    # 下午交易时间：13:00-15:00
    morning_start = datetime.strptime('09:30:00', '%H:%M:%S').time()
    morning_end = datetime.strptime('11:30:00', '%H:%M:%S').time()
    afternoon_start = datetime.strptime('13:00:00', '%H:%M:%S').time()
    afternoon_end = datetime.strptime('15:00:00', '%H:%M:%S').time()
    
    is_morning_trading = morning_start <= current_time <= morning_end
    is_afternoon_trading = afternoon_start <= current_time <= afternoon_end
    
    return is_morning_trading or is_afternoon_trading

# 后台服务主函数
def background_service():
    global running
    
    # 检查是否已有实例在运行
    if not check_lock_file():
        return
    
    running = True
    
    print("后台自动数据获取服务已启动")
    print(f"数据获取间隔: {FETCH_INTERVAL}秒")
    print("按 Ctrl+C 停止服务\n")
    
    try:
        while running:
            # 获取当前时间
            now = datetime.now()
            
            # 检查是否在交易时间内
            if not is_trading_time():
                print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 当前不在交易时间内，跳过本次数据获取")
                # 等待下一次检查
                for _ in range(FETCH_INTERVAL):
                    if not running:
                        break
                    time.sleep(1)
                continue
            
            print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 开始获取关注列表股票数据...")
            
            # 获取关注列表中的所有股票
            watchlist_items = session.query(Watchlist).all()
            
            if not watchlist_items:
                print("关注列表为空，跳过本次数据获取")
            else:
                print(f"关注列表中有 {len(watchlist_items)} 只股票")
                
                # 遍历关注列表，获取每只股票的数据
                for item in watchlist_items:
                    try:
                        print(f"获取股票: {item.stock_code} ({item.stock_name}) 数据...")
                        
                        # 获取股票数据
                        stock_info = get_stock_quote.get_stock_quote(item.stock_code)
                        
                        if stock_info:
                            # 存储数据到数据库
                            try:
                                stock_quote = StockQuote(
                                    stock_code=stock_info['股票代码'],
                                    stock_name=stock_info['股票名称'],
                                    market=stock_info['市场'],
                                    current_price=stock_info['当前价格'],
                                    change_price=stock_info['涨跌额'],
                                    change_percent=float(stock_info['涨跌幅'].replace('%', '')),
                                    open_price=stock_info['今日开盘价'],
                                    pre_close=stock_info['昨日收盘价'],
                                    high_price=stock_info['今日最高价'],
                                    low_price=stock_info['今日最低价'],
                                    volume=stock_info['成交量'],
                                    amount=stock_info['成交额'],
                                    buy1_price=stock_info['买一报价'],
                                    buy1_amount=stock_info['买一申报'],
                                    buy2_price=stock_info['买二报价'],
                                    buy2_amount=stock_info['买二申报'],
                                    buy3_price=stock_info['买三报价'],
                                    buy3_amount=stock_info['买三申报'],
                                    buy4_price=stock_info['买四报价'],
                                    buy4_amount=stock_info['买四申报'],
                                    buy5_price=stock_info['买五报价'],
                                    buy5_amount=stock_info['买五申报'],
                                    sell1_price=stock_info['卖一报价'],
                                    sell1_amount=stock_info['卖一申报'],
                                    sell2_price=stock_info['卖二报价'],
                                    sell2_amount=stock_info['卖二申报'],
                                    sell3_price=stock_info['卖三报价'],
                                    sell3_amount=stock_info['卖三申报'],
                                    sell4_price=stock_info['卖四报价'],
                                    sell4_amount=stock_info['卖四申报'],
                                    sell5_price=stock_info['卖五报价'],
                                    sell5_amount=stock_info['卖五申报'],
                                    date=stock_info['日期'],
                                    time=stock_info['时间']
                                )
                                session.add(stock_quote)
                                session.commit()
                                print(f"股票 {item.stock_code} 数据存储成功")
                            except Exception as db_error:
                                session.rollback()
                                print(f"股票 {item.stock_code} 数据存储失败: {db_error}")
                        else:
                            print(f"获取股票 {item.stock_code} 数据失败")
                    except Exception as e:
                        print(f"处理股票 {item.stock_code} 时出错: {e}")
                    
                    # 每只股票之间暂停1秒，避免请求过于频繁
                    time.sleep(1)
            
            # 打印本次获取完成的信息
            print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 关注列表股票数据获取完成")
            print(f"下次获取时间: {datetime.now().timestamp() + FETCH_INTERVAL}")
            print("-" * 60)
            
            # 等待下一次获取
            for _ in range(FETCH_INTERVAL):
                if not running:
                    break
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n后台自动数据获取服务正在停止...")
    finally:
        running = False
        print("后台自动数据获取服务已停止")

# 启动后台服务
def start_service():
    service_thread = threading.Thread(target=background_service, daemon=True)
    service_thread.start()
    return service_thread

# 停止后台服务
def stop_service():
    global running
    running = False

if __name__ == '__main__':
    background_service()
