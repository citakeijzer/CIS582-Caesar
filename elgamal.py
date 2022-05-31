import random

from params import p
from params import g

def keygen():
    sk = 0
    pk = 0
    return pk,sk

def encrypt(pk,m):
    c1 = 0
    c2 = 0
    return [c1,c2]

def decrypt(sk,c):
    m = 0
    return m


# Given ciphertext (c1,c2)
# Secret key a
# sk = a
# pk = g^a mod p
# Recovering the secret key from the public key is the same as solving the discrete log problem
# Ciphertext is (c1,c2) = (g^r mod p, h^r∙m mod p)
# >pow(x,y,n) Works for all numbers (uses square-and-multiply)
