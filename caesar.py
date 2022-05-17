
def encrypt(key,plaintext):
    ciphertext=""
    #YOUR CODE HERE
    for i in plaintext:
        new_ord = ord(i)+key
        if new_ord < 65:
            new_ord += 26
        elif new_ord > 90:
            new_ord -=26
        new_char = chr(new_ord)
        ciphertext += new_char
    return ciphertext



