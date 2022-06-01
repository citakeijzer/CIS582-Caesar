from fastecdsa.curve import secp256k1
from fastecdsa.keys import export_key, gen_keypair

from fastecdsa import curve, ecdsa, keys, point
from hashlib import sha256

def sign(m):
	#generate public key
	#Your code here
	secp = secp256k1
	private_key, public_key = gen_keypair(secp)

	#generate signature
	#Your code here
	r,s = ecdsa.sign(m, private_key, secp, sha256)

	assert isinstance( public_key, point.Point )
	assert isinstance( r, int )
	assert isinstance( s, int )
	return( public_key, [r,s] )

