import re
import hashlib
import unicodedata
import string
from os import path
import pathlib

from deezer.utils import map_album as d_map_album, map_artist_album, \
    map_playlist, map_user_album, \
    map_user_artist, map_user_playlist, map_user_track


def map_gw_track(track):
    album_id = track.get("ALB_ID")
    album_md5_cover = track.get("ALB_PICTURE")
    album = {"id": album_id, "md5_image": album_md5_cover}
    album["title"] = track.get("ALB_TITLE")
    album["cover"] = f"https://api.deezer.com/album/{album_id}/image"
    album["cover_small"] = f"https://e-cdns-images.dzcdn.net/images/cover/{album_md5_cover}/56x56-000000-80-0-0.jpg"
    album["cover_medium"] = f"https://e-cdns-images.dzcdn.net/images/cover/{album_md5_cover}/250x250-000000-80-0-0.jpg"
    album["cover_big"] = f"https://e-cdns-images.dzcdn.net/images/cover/{album_md5_cover}/500x500-000000-80-0-0.jpg"
    album["cover_xl"] = f"https://e-cdns-images.dzcdn.net/images/cover/{album_md5_cover}/1000x1000-000000-80-0-0.jpg"

    contributors = []
    role_map = {
        "0": "Main",
        "5": "Featured"
    }
    for art in track.get("ARTISTS", []):
        id = art.get("ART_ID")
        p = art.get("ART_PICTURE")

        contributors.append({
            "id": id,
            "name": art.get("ART_NAME"),
            "role": role_map.get(art.get("ROLE_ID", -1), "Unknown"),
            "is_dummy": art.get("ARTIST_IS_DUMMY"),
            "picture": f"https://api.deezer.com/artist/{id}/image",
            "picture_small": f"https://e-cdns-images.dzcdn.net/images/artist/{p}/56x56-000000-80-0-0.jpg",
            "picture_medium": f"https://e-cdns-images.dzcdn.net/images/artist/{p}/250x250-000000-80-0-0.jpg",
            "picture_big": f"https://e-cdns-images.dzcdn.net/images/artist/{p}/500x500-000000-80-0-0.jpg",
            "picture_xl": f"https://e-cdns-images.dzcdn.net/images/artist/{p}/1000x1000-000000-80-0-0.jpg",
            "rank": art.get("RANK"),
            "locales": art.get("LOCALES"),
            "smartradio": art.get("SMARTRADIO"),
            "type": art.get("__TYPE__")
        })

    main_artist = list(filter(lambda contributor: contributor.get(
        "role") == "Main", contributors))[0]

    digital_release_date = track.get("DIGITAL_RELEASE_DATE")
    physical_release_date = track.get("PHYSICAL_RELEASE_DATE")
    release_date = physical_release_date or digital_release_date

    explicit_track_content = track.get("EXPLICIT_TRACK_CONTENT")
    explicit_content = None

    if explicit_track_content:
        explicit_content = {}
        explicit_content["lyrics"] = explicit_track_content.get(
            "EXPLICIT_LYRICS_STATUS")
        explicit_content["cover"] = explicit_track_content.get(
            "EXPLICIT_COVER_STATUS")

    preview = None

    for medium in track.get("MEDIA", []):
        if medium.get("TYPE") == "preview":
            preview = medium.get("HREF")
            break

    return {
        "id": track.get("SNG_ID"),
        "title": track.get("SNG_TITLE"),
        "album": album,
        "contributors": contributors,
        "artist": main_artist,
        "md5_origin": track.get("MD5_ORIGIN"),
        "user_id": track.get("USER_ID"),
        "digital_release_date": digital_release_date,
        "physical_release_date": physical_release_date,
        "release_date": release_date,
        "track_number": track.get("TRACK_NUMBER"),
        "disk_number": track.get("DISK_NUMBER"),
        "duration": track.get("DURATION"),
        "explicit_lyrics": int(track.get("EXPLICIT_LYRICS", -1)) > 0,
        "explicit_content": explicit_content,
        "genre_id": track.get("GENRE_ID"),
        "hierarchical_title": track.get("HIERARCHICAL_TITLE"),
        "isrc": track.get("ISRC"),
        "lyrics_id": track.get("LYRICS_ID"),
        "provider_id": track.get("PROVIDER_ID"),
        "rank": track.get("RANK"),
        "smartradio": track.get("SMARTRADIO"),
        "status": track.get("STATUS"),
        "version": track.get("VERSION"),
        "gain": track.get("GAIN"),
        "media_version": track.get("MEDIA_VERSION"),
        "token": track.get("TRACK_TOKEN"),
        "token_expire": track.get("TRACK_TOKEN_EXPIRE"),
        "preview": preview,
        "type": track.get("__TYPE__")
    }


def map_api_track(track):
    return {
        "id": track.get("id"),
        "title": track.get("title"),
        "isrc": track.get("isrc"),
        "duration": track.get("duration"),
        "track_number": track.get("track_position"),
        "disk_number": track.get("disk_number"),
        "rank": track.get("rank"),
        "release_date": track.get("release_date"),
        "explicit_lyrics": track.get("explicit_lyrics"),
        "explicit_content": {
            "lyrics": track.get("explicit_content_lyrics"),
            "cover": track.get("explicit_content_cover")
        },
        "preview": track.get("preview"),
        "gain": track.get("gain"),
        "contributors": track.get("contributors"),
        "artist": track.get("artist"),
        "album": track.get("album"),
        "type": track.get("type")
    }


def map_gw_album(album):
    RELEASE_TYPE = {"single": 0, "album": 1,
                    "compile": 2, "ep": 3, "bundle": 4}

    album["TYPE"] = RELEASE_TYPE.get(album["__TYPE__"].lower(), -1)
    album["EXPLICIT_LYRICS"] = album["EXPLICIT_ALBUM_CONTENT"].get(
        "EXPLICIT_LYRICS_STATUS")

    album_mapped = d_map_album(album)
    album_mapped["label"] = album.get("LABEL_NAME")
    album_mapped["artist"] = {
        "id": album.get("ART_ID"),
        "name": album.get("ART_NAME")
    }
    album_mapped["copyright"] = album.get("COPYRIGHT")
    return album_mapped


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
