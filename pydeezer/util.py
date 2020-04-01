import re

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