from flask import Flask, request, g
from flask_restful import Resource, Api
from sqlalchemy import create_engine, select, MetaData, Table
from flask import jsonify
import json
import eth_account
import algosdk
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import load_only

from models import Base, Order, Log
engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)

#These decorators allow you to use g.session to access the database inside the request code
@app.before_request
def create_session():
    g.session = scoped_session(DBSession) #g is an "application global" https://flask.palletsprojects.com/en/1.1.x/api/#application-globals

@app.teardown_appcontext
def shutdown_session(response_or_exc):
    g.session.commit()
    g.session.remove()

"""
-------- Helper methods (feel free to add your own!) -------
"""

def log_message(d):
    # Takes input dictionary d and writes it to the Log table
    payload = d['payload']
    new_log = Log(message = json.dumps(payload)) 
    return new_log


"""
---------------- Endpoints ----------------
"""
    
@app.route('/trade', methods=['POST'])
def trade():
    if request.method == "POST":
        content = request.get_json(silent=True)
        print( f"content = {json.dumps(content)}" )
        columns = [ "sender_pk", "receiver_pk", "buy_currency", "sell_currency", "buy_amount", "sell_amount", "platform" ]
        fields = [ "sig", "payload" ]
        error = False
        for field in fields:
            if not field in content.keys():
                print( f"{field} not received by Trade" )
                print( json.dumps(content) )
                log_message(content)
                return jsonify( False )
        
        error = False
        for column in columns:
            if not column in content['payload'].keys():
                print( f"{column} not received by Trade" )
                error = True
        if error:
            print( json.dumps(content) )
            log_message(content)
            return jsonify( False )
            
        #Your code here
        #Note that you can access the database session using g.session
        
        verifier = False #
        payload = content['payload']
        platform = payload['platform']
        pk = payload['sender_pk']
        sig = content["sig"]

        if platform == 'Ethereum':
            msg_coded = eth_account.messages.encode_defunct(text = json.dumps(payload))
            pk_new = eth_account.Account.recover_message(msg_coded, signature = sig)
            if pk == pk_new:
                verifier = True
            else:
               print("Failed to verify - Eth")
                                                              
        elif platform == 'Algorand':
            if algosdk.util.verify_bytes(json.dumps(payload).encode('utf-8'),sig, pk):
                verifier = True
            else:
               print("Failed to verify - Algorand")
        else:
            print("Error: ", platform)
            print( json.dumps(content) )
            log_message(content)
            #return jsonify( False )
        
        if verifier == True: 
            add_order = Order(signature = sig, receiver_pk = payload['receiver_pk'], sender_pk = pk, buy_amount = payload['buy_amount'], sell_amount = payload['sell_amount'], buy_currency = payload['buy_currency'], sell_currency = payload['sell_currency'])
            g.session.add(add_order)
            g.session.commit()
            #return jsonify(True)
        else:
            log_message(content)
                                                              
        return jsonify(verifier) 
                                                              
@app.route('/order_book')
def order_book():
    #Your code here
    #Note that you can access the database session using g.session
    
    orders = g.session.query(Order)
    
    for order in orders:
        result = {'data':
                  [{'signature': order.signature,
                    'receiver_pk': order.receiver_pk,
                    'sender_pk': order.sender_pk,
                    'buy_amount': order.buy_amount,
                    'sell_amount': order.sell_amount,
                    'buy_currency': order.buy_currency,
                    'sell_currency': order.sell_currency} ]
                 }
                                                              
    return jsonify(result)

if __name__ == '__main__':
    app.run(port='5002')
