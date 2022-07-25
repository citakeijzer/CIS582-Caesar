#!/usr/bin/python3

from algosdk.v2client import algod
from algosdk import mnemonic
from algosdk import transaction

from algosdk import account, encoding

private_key, address = account.generate_account()
print("Private key:", private_key)
print("Public key:", public_key)

print("Address:", address)
      
#Connect to Algorand node maintained by PureStake
algod_address = "https://testnet-algorand.api.purestake.io/ps2"
algod_token = "B3SU4KcVKi94Jap2VXkK83xx38bsv95K5UZm2lab"
#algod_token = 'IwMysN3FSZ8zGVaQnoUIJ9RXolbQ5nRY62JRqF2H'
headers = {
   "X-API-Key": algod_token,
}

acl = algod.AlgodClient(algod_token, algod_address, headers)
min_balance = 100000 #https://developer.algorand.org/docs/features/accounts/#minimum-balance

address="7PGDWW3H2L5SCKR2DBJBEC3QYIVDOWYXYPCZLZ24246M5ZEY46ARQZ5WVU"
private_key="Pspk7L8vpAv/5qXUlzdnKt001R2x9rrk0MZNr3WB7lD7zDtbZ9L7ISo6GFISC3DCKjdbF8PFledc1zzO5JjngQ=="

def send_tokens( receiver_pk, tx_amount ):
    params = acl.suggested_params()
    gen_hash = params.gh
    first_valid_round = params.first
    tx_fee = params.min_fee
    last_valid_round = params.last

    #Your code here
    sender_pk = pk
    params.fee = tx_amount
    receiver = receiver_pk
    unsigned_txn = PaymentTxn(sender_pk, params, receiver_pk, tx_amount)
    signed_txn = unsigned_txn.sign(mnemonic.to_private_key(mnemonic1))
    txid = acl.send_transaction(signed_txn)
    print("Successfully sent transaction with txID: {}".format(txid))
    
    return sender_pk, txid

# Function from Algorand Inc.
def wait_for_confirmation(client, txid):
    """
    Utility function to wait until the transaction is
    confirmed before proceeding.
    """
    last_round = client.status().get('last-round')
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
        print("Waiting for confirmation")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    print("Transaction {} confirmed in round {}.".format(txid, txinfo.get('confirmed-round')))
    return txinfo

