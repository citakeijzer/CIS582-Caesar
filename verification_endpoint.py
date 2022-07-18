from flask import Flask, request, jsonify
from flask_restful import Api
import json
import eth_account
import algosdk

app = Flask(__name__)
api = Api(app)
app.url_map.strict_slashes = False

@app.route('/verify', methods=['GET','POST'])
    content = request.get_json(silent=True)

    print("Content: ", content)
    if content == None:
        return False

    payload = content.get('payload')
    signature = content.get('sig')
    platform = payload.get('platform')
    pk = payload.get('pk')
    message = payload.get('message')
        
    if platform == "Ethereum":
        encoded_msg = eth_account.messages.encode_defunct(text = json.dumps(payload))
        if eth_account.Account.recover_message(encoded_msg,signature=signature) == pk:
            result = True
        else:
            result = False
    else:
        if algosdk.util.verify_bytes(json.dumps(payload).encode('utf-8'), signature, pk) == True:
            result = True
        else:
            result = False
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(port='5002')
