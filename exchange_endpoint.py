from flask import Flask, request, g
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from flask import jsonify
from web3 import Web3
from send_tokens import connect_to_algo, connect_to_eth, send_tokens_algo, send_tokens_eth
from models import Base, Order, TX
import json
import eth_account
import algosdk
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import load_only
from datetime import datetime
import math
import sys
import traceback


w3 = connect_to_eth()
acl = connect_to_algo(connection_type="indexer")
bcl = connect_to_algo(connection_type="other")

engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)

""" Pre-defined methods (do not need to change) """


@app.before_request
def create_session():
    g.session = scoped_session(DBSession)


@app.teardown_appcontext
def shutdown_session(response_or_exc):
    sys.stdout.flush()
    g.session.commit()
    g.session.remove()


def connect_to_blockchains():
    try:
        acl_flag = False
        g.acl
    except AttributeError as ae:
        acl_flag = True

    try:
        if acl_flag or not g.acl.status():
            g.acl = connect_to_algo()
    except Exception as e:
        print("Trying to connect to algorand client again")
        print(traceback.format_exc())
        g.acl = connect_to_algo()

    try:
        icl_flag = False
        g.icl
    except AttributeError as ae:
        icl_flag = True

    try:
        if icl_flag or not g.icl.health():
            g.icl = connect_to_algo(connection_type='indexer')
    except Exception as e:
        print("Trying to connect to algorand indexer client again")
        print(traceback.format_exc())
        g.icl = connect_to_algo(connection_type='indexer')

    try:
        w3_flag = False
        g.w3
    except AttributeError as ae:
        w3_flag = True

    try:
        if w3_flag or not g.w3.isConnected():
            g.w3 = connect_to_eth()
    except Exception as e:
        print("Trying to connect to web3 again")
        print(traceback.format_exc())
        g.w3 = connect_to_eth()


""" End of pre-defined methods """


""" Helper Methods (skeleton code for you to implement) """


def fill_order(order):

    filtered = g.session.query(Order).filter(Order.filled == None).all()

    for selected in filtered:
        if selected.buy_currency == order.sell_currency and selected.sell_currency == order.buy_currency:
            if ((selected.sell_amount / selected.buy_amount) >= (order.buy_amount / order.sell_amount)):
                order.filled = datetime.now()
                selected.filled = datetime.now()
                order.counterparty_id = selected.id
                selected.counterparty_id = order.id
                txes = [order, selected]
                execute_txes(txes)
                if order.buy_amount > selected.sell_amount:
                    remainder = order.buy_amount - selected.sell_amount
                    exchange = order.buy_amount / order.sell_amount
                    dev_o = Order(creator_id=order.id,
                                              counterparty_id=None,
                                              sender_pk=order.sender_pk,
                                              receiver_pk=order.receiver_pk,
                                              buy_currency=order.buy_currency,
                                              sell_currency=order.sell_currency,
                                              buy_amount=remainder,
                                              sell_amount=remainder / exchange,
                                              filled=None)
                    g.session.add(dev_o)
                elif selected.buy_amount > order.sell_amount:
                    remainder = selected.buy_amount - order.sell_amount
                    exchange = selected.sell_amount / selected.buy_amount
                    dev_o = Order(creator_id=selected.id,
                                              counterparty_id=None,
                                              sender_pk=selected.sender_pk,
                                              receiver_pk=selected.receiver_pk,
                                              buy_currency=selected.buy_currency,
                                              sell_currency=selected.sell_currency,
                                              buy_amount=remainder, 
                                              sell_amount=remainder * exchange,
                                              filled=None)
                    g.session.add(dev_o)
                g.session.commit()
                break


def execute_txes(txes):
    if txes is None:
        return True
    if len(txes) == 0:
        return True
    print(f"Trying to execute {len(txes)} transactions")

    algo_sk, algo_pk = get_algo_keys()
    eth_sk, eth_pk = get_eth_keys()

    if not all(tx.sell_currency in ["Algorand", "Ethereum"] for tx in txes):
        print("Error: execute_txes got an invalid platform!")
        print(tx.sell_currency for tx in txes)

    order = txes[0]
    selected = txes[1]
    new_txes = []

    firsttx = {
        'platform': selected.buy_currency,
        'receiver_pk': selected.receiver_pk,
        'order_id': selected.id,
        'tx_id': 0,
        'send_amount': min(order.sell_amount, selected.buy_amount)
    }
    new_txes.append(firsttx)
    secondtx = {
        'platform': order.buy_currency,
        'receiver_pk': order.receiver_pk,
        'order_id': order.id,
        'tx_id': 0,
        'send_amount': min(order.buy_amount, selected.sell_amount)
    }
    new_txes.append(secondtx)

    algo_txes = [tx for tx in new_txes if tx['platform'] == "Algorand"]
    algo_TX_obj = TX(platform=algo_txes[0]['platform'],
                     receiver_pk=algo_txes[0]['receiver_pk'],
                     order_id=algo_txes[0]['order_id'],
                     tx_id=send_tokens_algo(bcl, algo_sk, algo_txes))
    eth_txes = [tx for tx in new_txes if tx['platform'] == "Ethereum"]
    eth_TX_obj = TX(platform=eth_txes[0]['platform'],
                    receiver_pk=eth_txes[0]['receiver_pk'],
                    order_id=eth_txes[0]['order_id'],
                    tx_id=send_tokens_eth(w3, eth_sk, eth_txes))
    g.session.add(algo_TX_obj)
    g.session.commit()
    g.session.add(eth_TX_obj)
    g.session.commit()



def attachList(order, data):
    data.append({
        'sender_pk': order.sender_pk,
        'receiver_pk': order.receiver_pk,
        'buy_currency': order.buy_currency,
        'sell_currency': order.sell_currency,
        'buy_amount': order.buy_amount,
        'sell_amount': order.sell_amount,
        'signature': order.signature,
        'tx_id': order.tx_id
    })


def check_sig(payload, sig):
    sender_public_key = payload['sender_pk']
    platform = payload['platform']
    payload = json.dumps(payload)
    if platform == 'Ethereum':
        msg_e = eth_account.messages.encode_defunct(text=payload)
        if eth_account.Account.recover_message(msg_e, signature=sig) == sender_public_key:
            return True
    elif platform == 'Algorand':
        if algosdk.util.verify_bytes(payload.encode('utf-8'), sig, sender_public_key):
            return True
    return False

def log_message(d):
    g.session.add(Log(logtime=datetime.now(), message=json.dumps(d)))
    g.session.commit()


def get_algo_keys():
    algo_sk = 'JnU3uxlyHBK5Dut5KSzkkYu+FauQeG0U/iGLMmn4bt04XRixztR3qSmFsGpJL4BUeggwv35632TAUBmfXlJzMQ=='
    algo_pk = 'HBORRMOO2R32SKMFWBVESL4AKR5AQMF7PZ5N6ZGAKAMZ6XSSOMY2IRKSHU'
    return algo_sk, algo_pk

def get_eth_keys(filename="eth_mnemonic.txt"):
    eth_pk = '0xca76a112701A240BDb038d45839BA18c3015EA2c'
    eth_sk = b'Q\x15+E\xa1\xde\x84\xa7\xa4\x80/\xaf.\xf0%|\xf2\xc9\x93\xf9\xf1\xb7\xf2\x92\xaa\x01\x14\x8b\x17b\xf5\xac'
    return eth_sk, eth_pk


def checker(payload, order):
    if order.sell_currency == "Ethereum":
        try:
            eth_tx = w3.eth.get_transaction(payload['tx_id'])
        except Exception as e:
            print(e)
            return False
        if eth_tx['from'] == payload['sender_pk'] and eth_tx['value'] == payload['sell_amount']:
            return True
    elif order.sell_currency == "Algorand":
        wait_for_confirmation_algo(connect_to_algo(), payload['tx_id'])
        algo_txes = acl.search_transactions(txid=payload['tx_id'])

        for algo_tx in algo_txes['transactions']:
            if algo_tx['payment-transaction']['amount'] == payload['sell_amount'] and algo_tx['sender'] == payload['sender_pk']:
                return True
    return False


""" End of Helper methods"""


@ app.route('/address', methods=['POST'])
def address():
    if request.method == "POST":
        content = request.get_json(silent=True)
        if 'platform' not in content.keys():
            print(f"Error: no platform provided")
            return jsonify("Error: no platform provided")
        if not content['platform'] in ["Ethereum", "Algorand"]:
            print(f"Error: {content['platform']} is an invalid platform")
            return jsonify(f"Error: invalid platform provided: {content['platform']}")

        if content['platform'] == "Ethereum":
            # Your code here
            eth_sk, eth_pk = get_eth_keys()
            return jsonify(eth_pk)
        if content['platform'] == "Algorand":
            # Your code here
            algo_sk, algo_pk = get_algo_keys()
            return jsonify(algo_pk)


@app.route('/trade', methods=['POST'])
def trade():
    print("In trade", file=sys.stderr)
    connect_to_blockchains()
    if request.method == "POST":
        content = request.get_json(silent=True)
        columns = ["buy_currency", "sell_currency", "buy_amount",
                   "sell_amount", "platform", "tx_id", "receiver_pk"]
        fields = ["sig", "payload"]
        error = False
        for field in fields:
            if not field in content.keys():
                print(f"{field} not received by Trade")
                error = True
        if error:
            print(json.dumps(content))
            return jsonify(False)

        error = False
        for column in columns:
            if not column in content['payload'].keys():
                print(f"{column} not received by Trade")
                error = True
        if error:
            print(json.dumps(content))
            return jsonify(False)

        payload = content['payload']
        sig = content['sig']
        checkSigResult = check_sig(payload, sig)
        if checkSigResult:
            order_obj = Order(sender_pk=payload['sender_pk'],
                              receiver_pk=payload['receiver_pk'],
                              buy_currency=payload['buy_currency'],
                              sell_currency=payload['sell_currency'],
                              buy_amount=payload['buy_amount'],
                              sell_amount=payload['sell_amount'],
                              signature=sig,
                              tx_id=payload['tx_id'])
            g.session.add(order_obj)
            g.session.commit()

            if checker(payload, order_obj) is False:
                return jsonify(False)

            fill_order(order_obj)
            log_message(content)

        else:
            log_message(content)

        return jsonify(checkSigResult)


@ app.route('/order_book')
def order_book():
    data = []

    for order in g.session.query(Order).all():
        attachList(order, data)
    return jsonify(data=data)


if __name__ == '__main__':
    app.run(port='5002')
