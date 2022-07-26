#!/usr/bin/python3

from algosdk.v2client import algod
from algosdk import mnemonic
from algosdk import transaction
from algosdk import account
from algosdk.future.transaction import PaymentTxn
import json

#Connect to Algorand node maintained by PureStake
algod_address = "https://testnet-algorand.api.purestake.io/ps2"
algod_token = "B3SU4KcVKi94Jap2VXkK83xx38bsv95K5UZm2lab"
#algod_token = 'IwMysN3FSZ8zGVaQnoUIJ9RXolbQ5nRY62JRqF2H'
headers = {
   "X-API-Key": algod_token,
}

acl = algod.AlgodClient(algod_token, algod_address, headers)
min_balance = 100000 #https://developer.algorand.org/docs/features/accounts/#minimum-balance

private_key, public_address = account.generate_account()
print("Base64 Private Key: {}\nPublic Algorand Address: {}\n".format(private_key, public_address))

pk="5KQHYWTFVZH3HA7VS6FK6AFMGCXNNT7YIEVRLYBCYJHOGIZHMV5EWSG4RU"
sk="xxpCSbUntUAc0JX0K0hOmxuqUnkVWJJU4vQAYuA+NivqoHxaZa5Ps4P1l4qvAKwwrtbP+EErFeAiwk7jIydleg=="


def send_tokens( receiver_pk, tx_amount ):
    params = acl.suggested_params()
    gen_hash = params.gh
    first_valid_round = params.first
    tx_fee = params.min_fee
    last_valid_round = params.last

    #Your code here
    tx = transaction.PaymentTxn(pk, tx_fee, first_valid_round, last_valid_round, gen_hash, receiver_pk, tx_amount)
    tx = tx.sign(sk)
    tx_id = acl.send_transaction(tx)
    sender_pk = pk 
    return sender_pk, tx_id

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

