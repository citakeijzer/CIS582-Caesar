from flask import Flask, request, g
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from flask import jsonify
import json
import eth_account
import algosdk
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import load_only
from datetime import datetime
import sys

from models import Base, Order, Log
engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)

@app.before_request
def create_session():
    g.session = scoped_session(DBSession)

@app.teardown_appcontext
def shutdown_session(response_or_exc):
    sys.stdout.flush()
    g.session.commit()
    g.session.remove()


""" Suggested helper methods """
def filterOrder(new_order):
    partya = g.session.query(Order).filter(Order.filled == None, Order.sell_currency == new_order.buy_currency, Order.buy_currency == new_order.sell_currency,((Order.sell_amount / Order.buy_amount) >= (new_order.buy_amount / new_order.sell_amount)), Order.sell_amount != Order.buy_amount, new_order.buy_amount != new_order.sell_amount)

    return partya.first()

def executeOrder(partyb, partya):
    partyb.filled = datetime.now()
    partya.filled = datetime.now()

    partyb.counterparty_id = partya.id
    partya.counterparty_id = partyb.id

    if partyb.buy_amount < partya.sell_amount:

        # Create a new order for remaining balance
        remaining = partya.sell_amount - partyb.buy_amount
        FX = partya.sell_amount / partya.buy_amount

        nextparty = Order(creator_id=partya.id, sender_pk=partya.sender_pk,
                                  receiver_pk=partya.receiver_pk,
                                  buy_currency=partya.buy_currency,
                                  sell_currency=partya.sell_currency,
                                  buy_amount= remaining / FX, sell_amount=remaining)
        g.session.add(nextparty)
        g.session.commit()

    elif partyb.buy_amount > partya.sell_amount:

        remaining = partyb.buy_amount - partya.sell_amount
        FX = partyb.buy_amount / partyb.sell_amount

        nextparty = Order(creator_id=partyb.id, sender_pk=partyb.sender_pk,
                                  receiver_pk=partyb.receiver_pk,
                                  buy_currency=partyb.buy_currency,
                                  sell_currency=partyb.sell_currency, buy_amount=remaining,
                                  sell_amount=remaining / FX)
        g.session.add(nextparty)
        g.session.commit()

    else:
        g.session.commit()

def recordData(order, data):
    data.append({
        'sender_pk': order.sender_pk,
        'receiver_pk': order.receiver_pk,
        'buy_currency': order.buy_currency,
        'sell_currency': order.sell_currency,
        'buy_amount': order.buy_amount,
        'sell_amount': order.sell_amount,
        'signature': order.signature
    })
    
def log_message(d):
    g.session.add(Log(logtime=datetime.now(), message=json.dumps(d)))
    g.session.commit()
    
def matchOrder(order):

    g.session.add(order)
    g.session.commit()
    partya = filterOrder(order)

    if (partya is not None):
        nextaccount = executeOrder(order, partya)
        if (nextaccount is not None):
            matchOrder(nextaccount)
    else:
        return 
""" End of helper methods """


@app.route('/trade', methods=['POST'])
def trade():
    print("In trade endpoint")
    if request.method == "POST":
        content = request.get_json(silent=True)
        print(f"content = {json.dumps(content)}")
        columns = ["sender_pk", "receiver_pk", "buy_currency",
                   "sell_currency", "buy_amount", "sell_amount", "platform"]
        fields = ["sig", "payload"]

        for field in fields:
            if not field in content.keys():
                print(f"{field} not received by Trade")
                print(json.dumps(content))
                log_message(content)
                return jsonify(False)

        for column in columns:
            if not column in content['payload'].keys():
                print(f"{column} not received by Trade")
                print(json.dumps(content))
                log_message(content)
                return jsonify(False)


        # Your code here
        # Note that you can access the database session using g.session
        signature = content['sig']
        payload = json.dumps(content['payload'])
        sender_public_key = content['payload']['sender_pk']
        receiver_public_key = content['payload']['receiver_pk']
        buy_currency = content['payload']['buy_currency']
        sell_currency = content['payload']['sell_currency']
        buy_amount = content['payload']['buy_amount']
        sell_amount = content['payload']['sell_amount']
        platform = content['payload']['platform']

        # TODO: Check the signature

        # TODO: Check the signature
        if platform == 'Ethereum':
            e_msg = eth_account.messages.encode_defunct(text=payload)
            if eth_account.Account.recover_message(e_msg, signature=signature) == sender_public_key:
                matchOrder(Order(sender_pk=sender_public_key, receiver_pk=receiver_public_key,
                                    buy_currency=buy_currency, sell_currency=sell_currency, buy_amount=buy_amount,
                                    sell_amount=sell_amount, signature=signature))
                return jsonify(True)
            else:
                log_message(content)
                return jsonify(False)
        elif platform == 'Algorand':
            if algosdk.util.verify_bytes(payload.encode('utf-8'), signature, sender_public_key):
                matchOrder(Order(sender_pk=sender_public_key, receiver_pk=receiver_public_key,
                                    buy_currency=buy_currency, sell_currency=sell_currency, buy_amount=buy_amount,
                                    sell_amount=sell_amount, signature=signature))
                return jsonify(True)
            else:
                log_message(content)
                return jsonify(False)


@app.route('/order_book')
def order_book():
    # Your code here
    # Note that you can access the database session using g.session
    data = []
    for order in g.session.query(Order).all():
        recordData(order, data)
    return jsonify(data=data)


if __name__ == '__main__':
    app.run(port='5002')
