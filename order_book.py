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
            subOrder = {}
            subOrder['sender_pk'] = firstmatch.sender_pk
            subOrder['receiver_pk'] = firstmatch.receiver_pk
            subOrder['sell_amount'] = firstmatch.sell_amount - neworder.buy_amount
            subOrder['buy_amount'] = ((firstmatch.sell_amount - neworder.buy_amount) * (firstmatch.buy_amount / firstmatch.sell_amount)
            subOrder['buy_currency'] = firstmatch.buy_currency
            subOrder['sell_currency'] = firstmatch.sell_currency
            subOrder['created_by'] = firstmatch.id
            process_order(subOrder)
        elif firstmatch.sell_amount < neworder.buy_amount:
            subOrder = {}
            subOrder['buy_currency'] = neworder.buy_currency
            subOrder['sell_currency'] = neworder.sell_currency
            subOrder['buy_amount'] = neworder.buy_amount - firstmatch.sell_amount
            subOrder['sell_amount'] = ((neworder.buy_amount - firstmatch.sell_amount) * (neworder.sell_amount / neworder.buy_amount)
            subOrder['sender_pk'] = neworder.sender_pk
            subOrder['receiver_pk'] = neworder.receiver_pk
            subOrder['created_by'] = firstmatch.id
            process_order(subOrder)
        else:
            break

