from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from models import Base, Order
engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

def process_order(order):
    # insert order
    fields = ['sender_pk','receiver_pk','buy_currency','sell_currency','buy_amount','sell_amount']
    order_obj = Order(**{f:order[f] for f in fields})
    session.add(order_obj)
    session.commit()
    session.refresh(order_obj)
    # print('inserted object id = ', order_obj.id)
    order_try_to_fill = order_obj
    while True:
        # q_dump = session.query(Order)
        # print('DUMP:')
        # for temp in q_dump.all():
        #     print(temp.__dict__)
        q = session.query(Order).filter(Order.filled == None).\
            filter(Order.sell_currency == order_try_to_fill.buy_currency).\
            filter(Order.buy_currency == order_try_to_fill.sell_currency).\
            filter(Order.sell_amount * order_try_to_fill.sell_amount >= Order.buy_amount * order_try_to_fill.buy_amount)
        if q.count() == 0:
            break
        found_order = q.first()
        # print('found one matched order:', found_order.__dict__)
        found_order.filled = datetime.now()
        order_try_to_fill.filled = datetime.now()
        found_order.counterparty_id = order_try_to_fill.id
        order_try_to_fill.counterparty_id = found_order.id
        if found_order.sell_amount > order_try_to_fill.buy_amount:
            child_order = {}
            child_order['buy_currency'] = found_order.buy_currency
            child_order['sell_currency'] = found_order.sell_currency
            child_order['sell_amount'] = found_order.sell_amount - order_try_to_fill.buy_amount
            child_order['buy_amount'] = ((found_order.sell_amount - order_try_to_fill.buy_amount) / found_order.sell_amount) * found_order.buy_amount
            child_order['sender_pk'] = found_order.sender_pk
            child_order['receiver_pk'] = found_order.receiver_pk
            child_order_obj = Order(**{f:child_order[f] for f in fields})
            child_order_obj.creator_id = found_order.id
            session.add_all([found_order, order_try_to_fill, child_order_obj])
            session.commit()
            session.refresh(child_order_obj)
            order_try_to_fill = child_order_obj
        elif found_order.sell_amount < order_try_to_fill.buy_amount:
            child_order = {}
            child_order['buy_currency'] = order_try_to_fill.buy_currency
            child_order['sell_currency'] = order_try_to_fill.sell_currency
            child_order['buy_amount'] = order_try_to_fill.buy_amount - found_order.sell_amount
            child_order['sell_amount'] = ((order_try_to_fill.buy_amount - found_order.sell_amount) / order_try_to_fill.buy_amount) * order_try_to_fill.sell_amount
            child_order['sender_pk'] = order_try_to_fill.sender_pk
            child_order['receiver_pk'] = order_try_to_fill.receiver_pk
            child_order_obj = Order(**{f:child_order[f] for f in fields})
            child_order_obj.creator_id = order_try_to_fill.id
            session.add_all([found_order, order_try_to_fill, child_order_obj])
            session.commit()
            session.refresh(child_order_obj)
            order_try_to_fill = child_order_obj
        else:
            break
