import requests
import json

from .constants import DEEZER_URL
from .constants import HTTP_HEADERS
from .constants import API_URL
from .constants import LEGACY_API_URL
from .constants import GET_USER_DATA
from .constants import GET_SUGGESTED_QUERIES

from .exceptions import LoginError
from .exceptions import APIRequestError

class Deezer:
    def __init__(self, arl=None):
        self.session = requests.session()
        self.user = None

        if arl:
            self.arl = arl
            self.loginViaArl(arl)

    def loginViaArl(self, arl):
        self.setCookie("arl", arl)
        self.getUserData()

        return self.user

    def getUserData(self):
        res = self.apiCall(GET_USER_DATA)
        data = res.json()["results"]

        self.token = data["checkForm"]

        if not data["USER"]["USER_ID"]:
            raise LoginError("Arl is invalid.")

        raw_user = data["USER"]

        if raw_user["USER_PICTURE"]:
            self.user = {
                "id": raw_user["USER_ID"],
                "name": raw_user["BLOG_NAME"],
                "arl": self.getCookies()["arl"],
                "image": "https://e-cdns-images.dzcdn.net/images/user/{0}/250x250-000000-80-0-0.jpg".format(raw_user["USER_PICTURE"])
            }
        else:
            self.user = {
                "id": raw_user["USER_ID"],
                "name": raw_user["BLOG_NAME"],
                "arl": self.getCookies()["arl"],
                "image": "https://e-cdns-images.dzcdn.net/images/user/250x250-000000-80-0-0.jpg"
            }

    def setCookie(self, key, value, domain=DEEZER_URL, path="/"):
        cookie = requests.cookies.create_cookie(
            name=key, value=value, domain=domain)
        self.session.cookies.set_cookie(cookie)

    def getCookies(self):
        if DEEZER_URL in self.session.cookies.list_domains():
            return self.session.cookies.get_dict(DEEZER_URL)
        return None

    def getSID(self):
        res = self.session.get(DEEZER_URL, headers=HTTP_HEADERS, cookies=self.getCookies())
        return res.cookies.get("sid", domain=".deezer.com")

    def getToken(self):
        if not self.token:
            self.getUserData()
        return self.token

    def apiCall(self, method, params={}):
        token = "null"
        if method != GET_USER_DATA:
            token = self.token

        res = self.session.post(API_URL, json=params, params={
            "api_version": "1.0",
            "api_token": token,
            "input": "3",
            "method": method
        }, headers=HTTP_HEADERS, cookies=self.getCookies())

        data = res.json()

        if data["error"]:
            error_type = list(data["error"].keys())[0]
            error_message = data["error"][error_type]
            raise APIRequestError("{0} : {1}".format(error_type, error_message))

        return res

    def legacyApiCall(self, method, params=None):
        res = self.session.get("{0}/{1}".format(LEGACY_API_URL, method), params=params, headers=HTTP_HEADERS, cookies=self.getCookies())
        
        data = res.json()

        if data["error"]:
            error_type = list(data["error"].keys())[0]
            error_message = data["error"][error_type]
            raise APIRequestError("{0} : {1}".format(error_type, error_message))

        return res

    def getSuggestedQueries(self, query):
        res = self.apiCall(GET_SUGGESTED_QUERIES, params={
            "QUERY": query
        })

        result_data = res.json()

        results = result_data["results"]["SUGGESTION"]
        for result in results:
            if "HIGHLIGHT" in result:
                del result["HIGHLIGHT"]

        return results
        