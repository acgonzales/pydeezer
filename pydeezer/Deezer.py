import json

import requests

from .constants import DEEZER_URL
from .constants import HTTP_HEADERS
from .constants import API_URL
from .constants import LEGACY_API_URL

from .constants import GET_USER_DATA
from .constants import GET_SUGGESTED_QUERIES
from .constants import SEARCH_TRACK
from .constants import SEARCH_ARTIST
from .constants import SEARCH_ALBUM
from .constants import SEARCH_PLAYLIST
from .constants import SONG_GET_DATA
from .constants import SONG_GET_LIST_DATA
from .constants import PAGE_TRACK
from .constants import ALBUM_GET_DATA
from .constants import PAGE_ARTIST
from .constants import PAGE_PLAYLIST

from .exceptions import LoginError
from .exceptions import APIRequestError

from . import util


class Deezer:
    def __init__(self, arl=None):
        self.session = requests.session()
        self.user = None

        if arl:
            self.arl = arl
            self.login_via_arl(arl)

    def login_via_arl(self, arl):
        self.set_cookie("arl", arl)
        self.get_user_data()

        return self.user

    def get_user_data(self):
        data = self._api_call(GET_USER_DATA)["results"]

        self.token = data["checkForm"]

        if not data["USER"]["USER_ID"]:
            raise LoginError("Arl is invalid.")

        raw_user = data["USER"]

        if raw_user["USER_PICTURE"]:
            self.user = {
                "id": raw_user["USER_ID"],
                "name": raw_user["BLOG_NAME"],
                "arl": self.get_cookies()["arl"],
                "image": "https://e-cdns-images.dzcdn.net/images/user/{0}/250x250-000000-80-0-0.jpg".format(raw_user["USER_PICTURE"])
            }
        else:
            self.user = {
                "id": raw_user["USER_ID"],
                "name": raw_user["BLOG_NAME"],
                "arl": self.get_cookies()["arl"],
                "image": "https://e-cdns-images.dzcdn.net/images/user/250x250-000000-80-0-0.jpg"
            }

    def set_cookie(self, key, value, domain=DEEZER_URL, path="/"):
        cookie = requests.cookies.create_cookie(
            name=key, value=value, domain=domain)
        self.session.cookies.set_cookie(cookie)

    def get_cookies(self):
        if DEEZER_URL in self.session.cookies.list_domains():
            return self.session.cookies.get_dict(DEEZER_URL)
        return None

    def get_sid(self):
        res = self.session.get(
            DEEZER_URL, headers=HTTP_HEADERS, cookies=self.get_cookies())
        return res.cookies.get("sid", domain=".deezer.com")

    def get_token(self):
        if not self.token:
            self.get_user_data()
        return self.token

    def get_track(self, track_id):
        method = SONG_GET_DATA
        params = {
            "SNG_ID": id
        }

        if not id < 0:
            method = PAGE_TRACK

        data = self._api_call(method, params=params)

        return data["results"]

    def get_tracks(self, track_ids):
        data = self._api_call(SONG_GET_LIST_DATA, params={
            "SNG_IDS": track_ids
        })

        data = data["results"]
        valid_ids = [str(song["SNG_ID"]) for song in data["data"]]

        data["errors"] = []
        for id in track_ids:
            if not str(id) in valid_ids:
                data["errors"].append(id)

        return data

    def get_album(self, album_id):
        data = self._api_call(ALBUM_GET_DATA, params={
            "ALB_ID": album_id,
            "LANG": "en"
        })

        return data["results"]

    def get_artist(self, artist_id):
        data = self._api_call(PAGE_ARTIST, params={
            "ART_ID": artist_id,
            "LANG": "en"
        })

        return data["results"]

    def get_playlist(self, playlist_id):
        data = self._api_call(PAGE_PLAYLIST, params={
            "playlist_id": playlist_id,
            "LANG": "en"
        })

        return data["results"]

    def get_suggested_queries(self, query):
        data = self._api_call(GET_SUGGESTED_QUERIES, params={
            "QUERY": query
        })

        results = data["results"]["SUGGESTION"]
        for result in results:
            if "HIGHLIGHT" in result:
                del result["HIGHLIGHT"]

        return results

    def search_tracks(self, query, limit=30, index=0):
        return self._legacy_search(SEARCH_TRACK, query, limit=limit, index=index)

    def search_albums(self, query, limit=30, index=0):
        return self._legacy_search(SEARCH_ALBUM, query, limit=limit, index=index)

    def search_artists(self, query, limit=30, index=0):
        return self._legacy_search(SEARCH_ARTIST, query, limit=limit, index=index)

    def search_playlists(self, query, limit=30, index=0):
        return self._legacy_search(SEARCH_PLAYLIST, query, limit=limit, index=index)

    def _legacy_search(self, method, query, limit=30, index=0):
        query = util.clean_query(query)

        data = self._legacy_api_call(method, {
            "q": query,
            "limit": limit,
            "index": index
        })

        return data["data"]

    def _api_call(self, method, params={}):
        token = "null"
        if method != GET_USER_DATA:
            token = self.token

        res = self.session.post(API_URL, json=params, params={
            "api_version": "1.0",
            "api_token": token,
            "input": "3",
            "method": method
        }, headers=HTTP_HEADERS, cookies=self.get_cookies())

        data = res.json()

        if "error" in data and data["error"]:
            error_type = list(data["error"].keys())[0]
            error_message = data["error"][error_type]
            raise APIRequestError(
                "{0} : {1}".format(error_type, error_message))

        return data

    def _legacy_api_call(self, method, params={}):
        res = self.session.get("{0}/{1}".format(LEGACY_API_URL, method),
                               params=params, headers=HTTP_HEADERS, cookies=self.get_cookies())

        data = res.json()

        if "error" in data and data["error"]:
            error_type = list(data["error"].keys())[0]
            error_message = data["error"][error_type]
            raise APIRequestError(
                "{0} : {1}".format(error_type, error_message))

        return data
