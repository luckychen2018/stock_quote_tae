from flask import Flask, render_template, request, jsonify
import get_stock_quote
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, time, date

app = Flask(__name__)

# 创建数据库引擎
engine = create_engine('sqlite:///stock_data.db', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

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
    morning_start = time(9, 30, 0)
    morning_end = time(11, 30, 0)
    afternoon_start = time(13, 0, 0)
    afternoon_end = time(15, 0, 0)
    
    is_morning_trading = morning_start <= current_time <= morning_end
    is_afternoon_trading = afternoon_start <= current_time <= afternoon_end
    
    return is_morning_trading or is_afternoon_trading

# 定义关注列表数据模型
class Watchlist(Base):
    __tablename__ = 'watchlist'
    
    id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), unique=True, index=True)
    stock_name = Column(String(50))
    market = Column(String(10))
    added_at = Column(DateTime, default=datetime.now)

# 定义股票行情数据模型
class StockQuote(Base):
    __tablename__ = 'stock_quotes'
    
    id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), index=True)
    stock_name = Column(String(50))
    market = Column(String(10))
    current_price = Column(Float)
    change_price = Column(Float)
    change_percent = Column(Float)
    open_price = Column(Float)
    pre_close = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    volume = Column(String(20))
    amount = Column(String(20))
    buy1_price = Column(Float)
    buy1_amount = Column(Integer)
    buy2_price = Column(Float)
    buy2_amount = Column(Integer)
    buy3_price = Column(Float)
    buy3_amount = Column(Integer)
    buy4_price = Column(Float)
    buy4_amount = Column(Integer)
    buy5_price = Column(Float)
    buy5_amount = Column(Integer)
    sell1_price = Column(Float)
    sell1_amount = Column(Integer)
    sell2_price = Column(Float)
    sell2_amount = Column(Integer)
    sell3_price = Column(Float)
    sell3_amount = Column(Integer)
    sell4_price = Column(Float)
    sell4_amount = Column(Integer)
    sell5_price = Column(Float)
    sell5_amount = Column(Integer)
    date = Column(String(10), index=True)
    time = Column(String(8))
    created_at = Column(DateTime, default=datetime.now)

# 创建表
Base.metadata.create_all(engine)

# 主页路由
@app.route('/')
def index():
    return render_template('index.html')

# 获取股票数据的API接口
@app.route('/api/stock/<stock_code>')
def get_stock_data(stock_code):
    session = Session()
    try:
        # 检查是否在交易时间内
        if is_trading_time():
            # 在交易时间内，实时获取股票数据
            stock_info = get_stock_quote.get_stock_quote(stock_code)
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
                except Exception as db_error:
                    session.rollback()
                    print(f"数据库存储失败: {db_error}")
                
                session.close()
                return jsonify(stock_info)
            else:
                session.close()
                return jsonify({'error': '获取股票数据失败'}), 404
        else:
            # 不在交易时间内，返回数据库中的最新数据
            latest_quote = session.query(StockQuote)\
                .filter_by(stock_code=stock_code)\
                .order_by(StockQuote.created_at.desc())\
                .first()
            
            if latest_quote:
                stock_info = {
                    '股票代码': latest_quote.stock_code,
                    '股票名称': latest_quote.stock_name,
                    '市场': latest_quote.market,
                    '当前价格': latest_quote.current_price,
                    '涨跌额': latest_quote.change_price,
                    '涨跌幅': f"{latest_quote.change_percent}%",
                    '今日开盘价': latest_quote.open_price,
                    '昨日收盘价': latest_quote.pre_close,
                    '今日最高价': latest_quote.high_price,
                    '今日最低价': latest_quote.low_price,
                    '成交量': latest_quote.volume,
                    '成交额': latest_quote.amount,
                    '买一报价': latest_quote.buy1_price,
                    '买一申报': latest_quote.buy1_amount,
                    '买二报价': latest_quote.buy2_price,
                    '买二申报': latest_quote.buy2_amount,
                    '买三报价': latest_quote.buy3_price,
                    '买三申报': latest_quote.buy3_amount,
                    '买四报价': latest_quote.buy4_price,
                    '买四申报': latest_quote.buy4_amount,
                    '买五报价': latest_quote.buy5_price,
                    '买五申报': latest_quote.buy5_amount,
                    '卖一报价': latest_quote.sell1_price,
                    '卖一申报': latest_quote.sell1_amount,
                    '卖二报价': latest_quote.sell2_price,
                    '卖二申报': latest_quote.sell2_amount,
                    '卖三报价': latest_quote.sell3_price,
                    '卖三申报': latest_quote.sell3_amount,
                    '卖四报价': latest_quote.sell4_price,
                    '卖四申报': latest_quote.sell4_amount,
                    '卖五报价': latest_quote.sell5_price,
                    '卖五申报': latest_quote.sell5_amount,
                    '日期': latest_quote.date,
                    '时间': latest_quote.time
                }
                session.close()
                return jsonify(stock_info)
            else:
                session.close()
                return jsonify({'error': '数据库中没有该股票的历史数据'}), 404
    except Exception as e:
        session.close()
        return jsonify({'error': str(e)}), 500

# 获取历史数据的API接口
@app.route('/api/stock/<stock_code>/history')
def get_stock_history(stock_code):
    session = Session()
    try:
        # 查询最近20条历史数据
        quotes = session.query(StockQuote)\
            .filter_by(stock_code=stock_code)\
            .order_by(StockQuote.created_at.desc())\
            .limit(20)\
            .all()\
        
        # 转换为JSON格式
        history_data = []
        for quote in quotes:
            history_data.append({
                'current_price': quote.current_price,
                'created_at': quote.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        session.close()
        return jsonify(history_data)
    except Exception as e:
        session.close()
        return jsonify({'error': str(e)}), 500

# 获取全天价格数据的API接口
@app.route('/api/stock/<stock_code>/day')
def get_stock_day_data(stock_code):
    session = Session()
    try:
        # 获取当天日期
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 查询当天的所有股票行情数据
        quotes = session.query(StockQuote)\
            .filter_by(stock_code=stock_code)\
            .filter(StockQuote.date == today)\
            .order_by(StockQuote.created_at.asc())\
            .all()\
        
        # 转换为JSON格式
        day_data = []
        for quote in quotes:
            day_data.append({
                'current_price': quote.current_price,
                'time': quote.time,
                'created_at': quote.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        session.close()
        return jsonify(day_data)
    except Exception as e:
        session.close()
        return jsonify({'error': str(e)}), 500

# 获取关注列表的API接口
@app.route('/api/watchlist')
def get_watchlist():
    session = Session()
    try:
        # 查询所有关注的股票
        watchlist_items = session.query(Watchlist).all()
        
        # 转换为JSON格式
        watchlist_data = []
        for item in watchlist_items:
            watchlist_data.append({
                'id': item.id,
                'stock_code': item.stock_code,
                'stock_name': item.stock_name,
                'market': item.market,
                'added_at': item.added_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        session.close()
        return jsonify(watchlist_data)
    except Exception as e:
        session.close()
        return jsonify({'error': str(e)}), 500

# 添加股票到关注列表的API接口
@app.route('/api/watchlist/add', methods=['POST'])
def add_to_watchlist():
    session = Session()
    try:
        data = request.json
        stock_code = data.get('stock_code')
        
        if not stock_code:
            session.close()
            return jsonify({'error': '股票代码不能为空'}), 400
        
        # 检查股票是否已在关注列表中
        existing_item = session.query(Watchlist).filter_by(stock_code=stock_code).first()
        if existing_item:
            session.close()
            return jsonify({'error': '股票已在关注列表中'}), 400
        
        # 获取股票信息
        stock_info = get_stock_quote.get_stock_quote(stock_code)
        if not stock_info:
            session.close()
            return jsonify({'error': '获取股票信息失败'}), 404
        
        # 添加到关注列表
        watchlist_item = Watchlist(
            stock_code=stock_info['股票代码'],
            stock_name=stock_info['股票名称'],
            market=stock_info['市场']
        )
        session.add(watchlist_item)
        session.commit()
        
        # 在关闭session之前获取所有需要的属性值
        watchlist_data = {
            'id': watchlist_item.id,
            'stock_code': watchlist_item.stock_code,
            'stock_name': watchlist_item.stock_name,
            'market': watchlist_item.market,
            'added_at': watchlist_item.added_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        session.close()
        return jsonify({
            'success': True,
            'message': '股票添加到关注列表成功',
            'data': watchlist_data
        })
    except Exception as e:
        session.rollback()
        session.close()
        return jsonify({'error': str(e)}), 500

# 从关注列表中删除股票的API接口
@app.route('/api/watchlist/remove/<int:item_id>', methods=['DELETE'])
def remove_from_watchlist(item_id):
    session = Session()
    try:
        # 查找关注列表项
        watchlist_item = session.query(Watchlist).filter_by(id=item_id).first()
        if not watchlist_item:
            session.close()
            return jsonify({'error': '关注列表项不存在'}), 404
        
        # 删除关注列表项
        session.delete(watchlist_item)
        session.commit()
        
        session.close()
        return jsonify({
            'success': True,
            'message': '股票从关注列表中删除成功'
        })
    except Exception as e:
        session.rollback()
        session.close()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
