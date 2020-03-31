import requests
import re

from . import constants
from .exceptions import LoginError
from .ens import User

class Deezer:
    def __init__(self, arl=None):
        self.session = requests.session()
        self.user = None
        
        if arl:
            self.loginViaArl(arl)

    def loginViaArl(self, arl):
        self.setCookie("arl", arl)
        self.getUserData()

        return self.user

    def getUserData(self):
        res = self.apiCall(constants.GET_USER_DATA)
        data = res.json()["results"]

        self.token = data["checkForm"]

        if not data["USER"]["USER_ID"]:
            raise LoginError("Arl is invalid.")

        raw_user = data["USER"]

        if raw_user["USER_PICTURE"]:
            self.user = User(raw_user["USER_ID"], raw_user["BLOG_NAME"], self.getCookies()["arl"], 
            "https://e-cdns-images.dzcdn.net/images/user/{0}/250x250-000000-80-0-0.jpg".format(raw_user["USER_PICTURE"]))
        else:
            self.user = User(raw_user["USER_ID"], raw_user["BLOG_NAME"], self.getCookies()["arl"])

    def setCookie(self, key, value, domain=constants.DEEZER_URL, path="/"):
        cookie=requests.cookies.create_cookie(
            name=key, value=value, domain=domain)
        self.session.cookies.set_cookie(cookie)

    def getCookies(self):
        if constants.DEEZER_URL in self.session.cookies.list_domains():
            return self.session.cookies.get_dict(constants.DEEZER_URL)
        return None

    def getSID(self):
        res = self.session.get(constants.DEEZER_URL, headers=constants.HTTP_HEADERS, cookies=self.getCookies())
        return res.cookies.get("sid", domain=".deezer.com")

    def getToken(self):
        if not self.token:
            self.getUserData()
        return self.token

    def apiCall(self, method, json=None):
        token="null"
        if method != constants.GET_USER_DATA:
            token=self.token

        res = self.session.post(constants.API_URL, json=json, data={
            "api_version": "1.0",
            "api_token": token,
            "input": "3",
            "method": method
        }, headers=constants.HTTP_HEADERS, cookies=self.getCookies())

        return res
