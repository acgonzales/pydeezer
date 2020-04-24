import re
import hashlib
import unicodedata
import string
from os import path
import pathlib


def clean_query(query):
    # A pure copy-paste of regex patterns from DeezloaderRemix
    # I dont know regex

    query = re.sub(r"/ feat[\.]? /g", " ", query)
    query = re.sub(r"/ ft[\.]? /g", " ", query)
    query = re.sub(r"/\(feat[\.]? /g", " ", query)
    query = re.sub(r"/\(ft[\.]? /g", " ", query)
    query = re.sub(r"/\&/g", "", query)
    query = re.sub(r"/–/g", "-", query)
    query = re.sub(r"/–/g", "-", query)

    return query


def create_folders(directory):
    directory = path.normpath(directory)

    p = pathlib.Path(directory)
    p.mkdir(parents=True, exist_ok=True)


def clean_filename(filename):
    # https://gist.github.com/wassname/1393c4a57cfcbf03641dbc31886123b8
    whitelist = "-_.() %s%s" % (string.ascii_letters,
                                string.digits) + "',&#$%@`~!^&+=[]{}"
    char_limit = 255
    replace = ''

    # replace spaces
    for r in replace:
        filename = filename.replace(r, '_')

    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize(
        'NFKD', filename).encode('ASCII', 'ignore').decode()

    # keep only whitelisted chars
    cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)
    if len(cleaned_filename) > char_limit:
        print("Warning, filename truncated because it was over {}. Filenames may no longer be unique".format(char_limit))
    return cleaned_filename[:char_limit]


def get_text_md5(text, encoding="UTF-8"):
    return hashlib.md5(str(text).encode(encoding)).hexdigest()


def get_blowfish_key(track_id):
    secret = 'g4el58wc0zvf9na1'

    m = hashlib.md5()
    m.update(bytes([ord(x) for x in track_id]))
    id_md5 = m.hexdigest()

    blowfish_key = bytes(([(ord(id_md5[i]) ^ ord(id_md5[i+16]) ^ ord(secret[i]))
                           for i in range(16)]))

    return blowfish_key
