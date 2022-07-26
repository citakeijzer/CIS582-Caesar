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

        if firstmatch.sell_amount < neworder.buy_amount:
            suborder = {}
            suborder['sender_pk'] = neworder.sender_pk
            suborder['receiver_pk'] = neworder.receiver_pk
            suborder['buy_currency'] = neworder.buy_currency
            suborder['sell_currency'] = neworder.sell_currency
            suborder['buy_amount'] = neworder.buy_amount - firstmatch.sell_amount
            suborder['sell_amount'] = (neworder.buy_amount - firstmatch.sell_amount) * (neworder.sell_amount / neworder.buy_amount)
            suborder_obj = Order(**{f:suborder[f] for f in fields})
            suborder_obj.creator_id = firstmatch.id
            session.add_all([suborder_obj, firstmatch, neworder])
            session.commit()
            session.refresh(suborder_obj)
            neworder = suborder_obj
        elif firstmatch.sell_amount > neworder.buy_amount:
            suborder = {}
            suborder['sender_pk'] = firstmatch.sender_pk
            suborder['receiver_pk'] = firstmatch.receiver_pk
            suborder['buy_currency'] = firstmatch.buy_currency
            suborder['sell_currency'] = firstmatch.sell_currency
            suborder['sell_amount'] = firstmatch.sell_amount - neworder.buy_amount
            suborder['buy_amount'] = (firstmatch.sell_amount - neworder.buy_amount)  * (firstmatch.buy_amount / firstmatch.sell_amount)
            suborder_obj = Order(**{f:suborder[f] for f in fields})
            suborder_obj.creator_id = neworder.id
            session.add_all([suborder_obj, firstmatch, neworder])
            session.commit()
            session.refresh(suborder_obj)
            neworder = suborder_obj
        else:
            break

