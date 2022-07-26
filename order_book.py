from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from models import Base, Order
engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

def process_order(order):
    #Your code here
    newOrder["counterparty_id"] = None
    newOrder["filled"] = None
    
    order_obj = Order(buy_currency = newOrder['buy_currency'], sell_currency = newOrder['sell_currency'], buy_amount = newOrder['buy_amount'], sell_amount = newOrder['sell_amount'], sender_pk = newOrder['sender_pk'], receiver_pk = newOrder['receiver_pk'] )

    session.add(order_obj)
    session.commit()
    session.refresh(order_obj)
    
    pending_order = order_obj
    
    while True:
        #filter out unfilled orders
        matching_orders = session.query(Order).filter(Order.filled == None).\
            filter(Order.sell_currency == pending_order.buy_currency).\
            filter(Order.buy_currency == pending_order.sell_currency).\
            filter(Order.sell_amount * pending_order.sell_amount >= Order.buy_amount * pending_order.buy_amount)
        #if no matching order, quit
        if matching_orders.count() == 0:
            break
        #use first order for matching
        matched_order = matching_orders.first()
        #record counterparty info
        matched_order.counterparty_id = pending_order.id
        matched_order.filled = datetime.now()
        pending_order.counterparty_id = matched_order.id
        pending_order.filled = datetime.now()
        
        if matched_order.sell_amount > pending_order.buy_amount:
            suborder = {}
            suborder['buy_currency'] = matched_order.buy_currency
            suborder['sell_currency'] = matched_order.sell_currency
            suborder['sell_amount'] = matched_order.sell_amount - pending_order.buy_amount
            suborder['buy_amount'] = ((matched_order.sell_amount - pending_order.buy_amount) / matched_order.sell_amount) * matched_order.buy_amount
            suborder['sender_pk'] = matched_order.sender_pk
            suborder['receiver_pk'] = matched_order.receiver_pk
            suborder_obj = Order(**{f:suborder[f] for f in fields})
            suborder_obj.creator_id = matched_order.id
            session.add_all([matched_order, pending_order, suborder_obj])
            session.commit()
            session.refresh(suborder_obj)
            pending_order = suborder_obj
        elif matched_order.sell_amount < pending_order.buy_amount:
            suborder = {}
            suborder['buy_currency'] = pending_order.buy_currency
            suborder['sell_currency'] = pending_order.sell_currency
            suborder['buy_amount'] = pending_order.buy_amount - matched_order.sell_amount
            suborder['sell_amount'] = ((pending_order.buy_amount - matched_order.sell_amount) / pending_order.buy_amount) * pending_order.sell_amount
            suborder['sender_pk'] = pending_order.sender_pk
            suborder['receiver_pk'] = pending_order.receiver_pk
            suborder_obj = Order(**{f:suborder[f] for f in fields})
            suborder_obj.creator_id = pending_order.id
            session.add_all([matched_order, pending_order, suborder_obj])
            session.commit()
            session.refresh(suborder_obj)
            pending_order = suborder_obj
        else:
            break

