import random

from params import p
from params import g

# if   q  is unknown, it suffices to generate   a  uniformly in the range   1,…,p , 
def keygen():
    q = int ((p − 1)/2) 
    a = random.SystemRandom().randint(1, q)
    h = pow(g, a, p)
    sk = a
    pk = h
    return pk,sk

def encrypt(pk,m):
    q = int ((p − 1)/2) 
    a = random.SystemRandom().randint(1, q)
    c1 = pow(g, r, p)
    h = pk
    c2 = pow(h, r, p) * m % p
    return [c1,c2]

def decrypt(sk,c):
    # m =c2 * c1^-a mod p
    a = sk
    m = pow(c[0],-a,p) * c[1] % p
    return m


# Given ciphertext (c1,c2)
# Secret key a
# sk = a
# pk = g^a mod p
# Recovering the secret key from the public key is the same as solving the discrete log problem
# Ciphertext is (c1,c2) = (g^r mod p, h^r∙m mod p)
# >pow(x,y,n) Works for all numbers (uses square-and-multiply)
