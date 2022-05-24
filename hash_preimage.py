import hashlib
import os

def hash_preimage(target_string):
    if not all( [x in '01' for x in target_string ] ):
        print( "Input should be a string of bits" )
        return
    nonce = b'\x00'
    
    k = len(target_string)
    target_k = target_string[-k:]

    while continueSearch:
        testcase = os.urandom(64)
        testcase_hex = hashlib.sha256(testcase).hexdigest()
        testcase_int = int(testcase_hex,16)
        testcase_bin = bin(testcase_int)
        testcase_bin_k = testcase_bin[-k:]
      
        if testcase_bin_k == target_k:
            nonce = testcase
            continueSearch = False
    
    return( nonce )

