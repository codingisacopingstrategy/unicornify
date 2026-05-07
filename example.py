import hashlib
from avatar import create_avatar
from sys import argv


def unicorn_for_email(email):
    hash = hashlib.md5(email).hexdigest()
    # Creates a BMP file of 256x256 pixels (see docstring of create_avatar)
    f = open("%s.bmp" % email.decode('utf-8'), "wb")
    f.write(create_avatar(128, int(hash, 16)))
    f.close()


if __name__ == "__main__":
    """Usage: python3 example.py
       Optional argument: e-mail address."""
    address = b'alice@example.com'
    if len(argv) == 2:
        address = argv[1].encode('utf-8')
    unicorn_for_email(address)
