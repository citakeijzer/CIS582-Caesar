import hashlib
import os

def hash_collision(k):
    if not isinstance(k,int):
        print( "hash_collision expects an integer" )
        return( b'\x00',b'\x00' )
    if k < 0:
        print( "Specify a positive number of bits" )
        return( b'\x00',b'\x00' )
   
    #Collision finding code goes here
    x = b'\x00'
    y = b'\x00'
    
    continueSearch = True
    database = {}
    
    while continueSearch:
      testcase = os.urandom(64)
      testcase_hex = hashlib.sha256(testcase).hexdigest()
      testcase_int = int(testcase_hex,16)
      testcase_bin_k = bin(testcase_int)[-k:]
      
      if testcase_bin_k in database:
        x = database[testcase_bin_k]
        y = testcase
        continueSearch = False
      else: 
        database[testcase_bin_k] = testcase
    
    return( x, y )
