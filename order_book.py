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
    neworder = order_obj
    while 1:
        matchedorders = session.query(Order).filter(Order.buy_amount * neworder.buy_amount <= Order.sell_amount * neworder.sell_amount).\
            filter(Order.sell_currency == neworder.buy_currency).\
            filter(Order.buy_currency == neworder.sell_currency).\
            filter(Order.filled == None)
        if matchedorders.count() == 0:
            break
        firstmatch = matchedorders.first()
        firstmatch.filled = datetime.now()
        firstmatch.counterparty_id = neworder.id
        neworder.filled = datetime.now()
        neworder.counterparty_id = firstmatch.id
        if firstmatch.sell_amount > neworder.buy_amount:
            sub_order = {}
            sub_order['buy_currency'] = firstmatch.buy_currency
            sub_order['sell_currency'] = firstmatch.sell_currency
            sub_order['sell_amount'] = firstmatch.sell_amount - neworder.buy_amount
            sub_order['buy_amount'] = ((firstmatch.sell_amount - neworder.buy_amount) / firstmatch.sell_amount) * firstmatch.buy_amount
            sub_order['sender_pk'] = firstmatch.sender_pk
            sub_order['receiver_pk'] = firstmatch.receiver_pk
            sub_order_obj = Order(**{f:sub_order[f] for f in fields})
            sub_order_obj.creator_id = firstmatch.id
            session.add_all([firstmatch, neworder, sub_order_obj])
            session.commit()
            session.refresh(sub_order_obg)
            neworder = sub_order_obj
        elif firstmatch.sell_amount < neworder.buy_amount:
            sub_order = {}
            sub_order['buy_currency'] = neworder.buy_currency
            sub_order['sell_currency'] = neworder.sell_currency
            sub_order['buy_amount'] = neworder.buy_amount - firstmatch.sell_amount
            sub_order['sell_amount'] = ((neworder.buy_amount - firstmatch.sell_amount) / neworder.buy_amount) * neworder.sell_amount
            sub_order['sender_pk'] = neworder.sender_pk
            sub_order['receiver_pk'] = neworder.receiver_pk
            sub_order_obj = Order(**{f:sub_order[f] for f in fields})
            sub_order_obj.creator_id = neworder.id
            session.add_all([firstmatch, neworder, sub_order_obj])
            session.commit()
            session.refresh(sub_order_obj)
            neworder = sub_order_obj
        else:
            break
