from functools import partial
import json
import hashlib
from os import path

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import mutagen
from mutagen import File
from mutagen.id3 import ID3, APIC
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

from .constants import *

from .exceptions import LoginError
from .exceptions import APIRequestError
from .exceptions import DownloadLinkDecryptionError

from . import util


class Deezer:
    def __init__(self, arl=None):
        """Instantiates a Deezer object
        
        Keyword Arguments:
            arl {str} -- Login using the given arl (default: {None})
        """


        self.session = requests.session()
        self.user = None

        if arl:
            self.arl = arl
            self.login_via_arl(arl)

    def login_via_arl(self, arl):
        """Logs in to Deezer using the given
        
        Arguments:
            arl {[type]} -- [description]
        
        Returns:
            dict -- User data given by the Deezer API
        """


        self.set_cookie("arl", arl)
        self.get_user_data()

        return self.user

    def get_user_data(self):
        """Gets the data of the user, this will only work arl is the cookie. Make sure you have run login_via_arl() before using this.
        
        Raises:
            LoginError: Will raise if the arl given is not identified by Deezer
        """


        data = self._api_call(api_methods.GET_USER_DATA)["results"]

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

    def set_cookie(self, key, value, domain=api_urls.DEEZER_URL, path="/"):
        """Sets the cookie in the given domain
        
        Arguments:
            key {str} -- The key of the cookie
            value {str} -- The value of the cookie
        
        Keyword Arguments:
            domain {str} -- The domain of the cookie (default: {api_urls.DEEZER_URL})
            path {str} -- The path of the cookie (default: {"/"})
        """


        cookie = requests.cookies.create_cookie(
            name=key, value=value, domain=domain)
        self.session.cookies.set_cookie(cookie)

    def get_cookies(self):
        """Get cookies in the domain of {api_urls.DEEZER_URL}
        
        Returns:
            dict -- Cookies
        """


        if api_urls.DEEZER_URL in self.session.cookies.list_domains():
            return self.session.cookies.get_dict(api_urls.DEEZER_URL)
        return None

    def get_sid(self):
        """Gets the SID of the current {session}
        
        Returns:
            str -- SID
        """


        res = self.session.get(
            api_urls.API_URL, headers=networking_settings.HTTP_HEADERS, cookies=self.get_cookies())
        return res.cookies.get("sid", domain=".deezer.com")

    def get_token(self):
        """Gets the token of the current {session}
        
        Returns:
            str -- Token
        """


        if not self.token:
            self.get_user_data()
        return self.token

    def get_track(self, track_id):
        """Gets the track info using the Deezer API
        
        Arguments:
            track_id {str} -- Track Id
        
        Returns:
            dict -- Dictionary that contains the {info}, {download} partial function, {tags}, and {get_tag} partial function.
        """


        method = api_methods.SONG_GET_DATA
        params = {
            "SNG_ID": track_id
        }

        if not int(track_id) < 0:
            method = api_methods.PAGE_TRACK

        data = self._api_call(method, params=params)
        data = data["results"]

        return {
            "info": data,
            "download": partial(self.download_track, data),
            "tags": self.get_track_tags(data),
            "get_tag": partial(self.get_track_tags, data)
        }

    def get_track_valid_quality(self, track):
        """Gets the valid download qualities of the given track
        
        Arguments:
            track {dict} -- Track dictionary, similar to the {info} value that is returned {using get_track()}
        
        Returns:
            list -- List of keys of the valid qualities from the {track_formats.TRACK_FORMAT_MAP}
        """
        if "DATA" in track:
            track = track["DATA"]

        qualities = []
        for key in track_formats.TRACK_FORMAT_MAP:
            k = f"FILESIZE_{key}"
            if k in track:
                if str(track[k]) != "0":
                    qualities.append(key)

        return qualities

    def get_track_tags(self, track, separator=", "):
        """Gets the possible ID3 tags of the track.
        
        Arguments:
            track {dict} -- Track dictionary, similar to the {info} value that is returned {using get_track()}
        
        Keyword Arguments:
            separator {str} -- Separator to separate multiple artists (default: {", "})
        
        Returns:
            dict -- Tags
        """


        if "DATA" in track:
            track = track["DATA"]

        album_data = self.get_album(track["ALB_ID"])

        main_artists = track["SNG_CONTRIBUTORS"]["main_artist"]
        artists = main_artists[0]
        for i in range(1, len(main_artists)):
            artists += separator + main_artists[i]

        title = track["SNG_TITLE"]
        if "featuring" in track["SNG_CONTRIBUTORS"]:
            featuring_artists_data = track["SNG_CONTRIBUTORS"]["featuring"]
            featuring_artists = featuring_artists_data[0]
            for i in range(1, len(featuring_artists_data)):
                featuring_artists += separator + featuring_artists_data[i]

            title += f" (feat. {featuring_artists})"

        total_tracks = album_data["NUMBER_TRACK"]
        track_number = str(track["TRACK_NUMBER"]) + "/" + str(total_tracks)

        cover = self.get_album_poster(album_data, size=1000)

        # TODO: I'd like to put some genre here, let me figure it out later
        tags = {
            "title": title,
            "artist": artists,
            "album": track["ALB_TITLE"],
            "albumartist": track["ART_NAME"],
            "label": album_data["LABEL_NAME"],
            "date": track["PHYSICAL_RELEASE_DATE"],
            "discnumber": track["DISK_NUMBER"],
            "tracknumber": track_number,
            "isrc": track["ISRC"],
            "copyright": track["COPYRIGHT"],
            "_albumart": cover, 
        }

        if "author" in track["SNG_CONTRIBUTORS"]:
            _authors = track["SNG_CONTRIBUTORS"]["author"]

            authors = _authors[0]
            for i in range(1, len(_authors)):
                authors += separator + _authors[i]

            tags["author"] = authors

        return tags

    def get_track_download_url(self, track, quality=None, renew=False):
        """Gets and decrypts the download url of the given track in the given quality
        
        Arguments:
            track {dict} -- Track dictionary, similar to the {info} value that is returned {using get_track()}
        
        Keyword Arguments:
            quality {str} -- Use values from {constants.track_formats}, will get the default quality if None or an invalid is given. (default: {None})
            renew {bool} -- Will renew the track object (default: {False})
        
        Raises:
            DownloadLinkDecryptionError: Will be raised if the track dictionary does not have an MD5
            ValueError: Will be raised if valid track argument was given
        
        Returns:
            str -- Download url
        """

        # Decryption algo got from: https://git.fuwafuwa.moe/toad/ayeBot/src/branch/master/bot.py;
        # and https://notabug.org/deezpy-dev/Deezpy/src/master/deezpy.py
        # Huge thanks!

        if renew:
            track = self.get_track(track["SNG_ID"])["info"]

        try:
            # Just in case they passed in the whole dictionary from get_track()
            if "DATA" in track:
                track = track["DATA"]
            if not "MD5_ORIGIN" in track:
                raise DownloadLinkDecryptionError(
                    "MD5 is needed to decrypt the download link.")

            md5_origin = track["MD5_ORIGIN"]
            track_id = track["SNG_ID"]
            media_version = track["MEDIA_VERSION"]
        except ValueError:
            raise ValueError(
                "You have passed an invalid argument. This method needs the \"DATA\" value in the dictionary returned by the get_track() method.")

        quality = self._select_valid_quality(track, quality)

        magic_char = "¤"
        step1 = magic_char.join((md5_origin,
                                 str(quality["code"]),
                                 track_id,
                                 media_version))
        m = hashlib.md5()
        m.update(bytes([ord(x) for x in step1]))

        step2 = m.hexdigest() + magic_char + step1 + magic_char
        step2 = step2.ljust(80, " ")

        cipher = Cipher(algorithms.AES(bytes('jo6aey6haid2Teih', 'ascii')),
                        modes.ECB(), default_backend())

        encryptor = cipher.encryptor()
        step3 = encryptor.update(bytes([ord(x) for x in step2])).hex()

        cdn = track["MD5_ORIGIN"][0]

        return f'https://e-cdns-proxy-{cdn}.dzcdn.net/mobile/1/{step3}'

    def download_track(self, track, download_dir, quality=None, filename=None, renew=False, with_metadata=True, with_lyrics=True, tag_separator=", "):
        """Downloads the given track
        
        Arguments:
            track {dict} -- Track dictionary, similar to the {info} value that is returned {using get_track()}
            download_dir {str} -- Directory (without {filename}) where the file is to be saved.
        
        Keyword Arguments:
            quality {str} -- Use values from {constants.track_formats}, will get the default quality if None or an invalid is given. (default: {None})
            filename {str} -- Filename with or without the extension (default: {None})
            renew {bool} -- Will renew the track object (default: {False})
            with_metadata {bool} -- If true, will write id3 tags into the file. (default: {True})
            with_lyrics {bool} -- If true, will find and save lyrics of the given track. (default: {True})
            tag_separator {str} -- Separator to separate multiple artists (default: {", "})
        """
        

        if with_lyrics:
            if "LYRICS" in track:
                lyric_data = track["LYRICS"]
            else:
                try:
                    if "DATA" in track:
                        lyric_data = self.get_track_lyrics(track["DATA"]["SNG_ID"])["info"]
                    else:
                        lyric_data = self.get_track_lyrics(track["SNG_ID"])["info"]
                except APIRequestError:
                    with_lyrics = False
        
        if "DATA" in track:
            track = track["DATA"]

        tags = self.get_track_tags(track, separator=tag_separator)

        url = self.get_track_download_url(track, quality, renew=renew)
        blowfish_key = util.get_blowfish_key(track["SNG_ID"])

        quality = self._select_valid_quality(track, quality)

        title = tags["title"]
        ext = quality["ext"]

        if not filename:
            filename = title + ext

        if not str(filename).endswith(ext):
            filename += ext

        download_dir = path.normpath(download_dir)
        download_path = path.join(download_dir, filename)

        print("Starting download of:", title)

        res = self.session.get(url, cookies=self.get_cookies(), stream=True)
        current_filesize = 0
        i = 0

        with open(download_path, "wb") as f:
            f.seek(current_filesize)

            for chunk in res.iter_content(2048):
                if i % 3 > 0:
                    f.write(chunk)
                elif len(chunk) < 2048:
                    f.write(chunk)
                    break
                else:
                    cipher = Cipher(algorithms.Blowfish(blowfish_key),
                                    modes.CBC(bytes([i for i in range(8)])),
                                    default_backend())

                    decryptor = cipher.decryptor()
                    dec_data = decryptor.update(chunk) + decryptor.finalize()
                    f.write(dec_data)
                i += 1

        if with_metadata:
            if ext.lower() == ".flac":
                self._write_flac_tags(download_path, track, tags=tags)
            else:
                self._write_mp3_tags(download_path, track, tags=tags)
        
        if with_lyrics:
            lyrics_path = path.join(download_dir, title)
            self.save_lyrics(lyric_data, lyrics_path)

        print("Track downloaded to:", download_path)

    def get_tracks(self, track_ids):
        """Gets the list of the tracks that corresponds with the given {track_ids}
        
        Arguments:
            track_ids {list} -- List of track id
        
        Returns:
            dict -- List of tracks
        """


        data = self._api_call(api_methods.SONG_GET_LIST_DATA, params={
            "SNG_IDS": track_ids
        })

        data = data["results"]
        valid_ids = [str(song["SNG_ID"]) for song in data["data"]]

        data["errors"] = []
        for id in track_ids:
            if not str(id) in valid_ids:
                data["errors"].append(id)

        return data

    def get_track_lyrics(self, track_id):
        """Gets the lyrics data of the given {track_id}
        
        Arguments:
            track_id {str} -- Track Id
        
        Returns:
            dict -- Dictionary that containts the {info}, and {save} partial function.
        """


        data = self._api_call(api_methods.SONG_LYRICS, params={
            "SNG_ID": track_id
        })
        data = data["results"]

        return {
            "info": data,
            "save": partial(self.save_lyrics, data)
        }

    def save_lyrics(self, lyric_data, save_path):
        """Saves the {lyric_data} into a .lrc file.
        
        Arguments:
            lyric_data {dict} -- The 'info' value returned from {get_track_lyrics()}
            save_path {str} -- Full path on where the file is to be saved
        
        Returns:
            bool -- Operation success
        """


        if not str(save_path).endswith(".lrc"):
            save_path += ".lrc"

        with open(save_path, "w") as f:
            sync_data = lyric_data["LYRICS_SYNC_JSON"]

            for line in sync_data:
                if str(line["line"]):
                    f.write("{0}{1}".format(
                        line["lrc_timestamp"], line["line"]))
                f.write("\n")

        return True

    def get_album(self, album_id):
        """Gets the album data of the given {album_id}
        
        Arguments:
            album_id {str} -- Album Id
        
        Returns:
            dict -- Album data
        """


        data = self._api_call(api_methods.ALBUM_GET_DATA, params={
            "ALB_ID": album_id,
            "LANG": "en"
        })

        return data["results"]

    def get_album_poster(self, album, size=500, ext="jpg"):
        """Gets the album poster as a binary data
        
        Arguments:
            album {dict} -- Album data
        
        Keyword Arguments:
            size {int} -- Size of the image, {size}x{size} (default: {500})
            ext {str} -- Extension of the image, can be ('.jpg' or '.png') (default: {"jpg"})
        
        Returns:
            bytes -- Binary data of the image
        """


        return self._get_poster(album["ALB_PICTURE"], size=size, ext=ext)

    def get_album_tracks(self, album_id):
        """Gets the tracks of the given {album_id}
        
        Arguments:
            album_id {str} -- Album Id
        
        Returns:
            list -- List of tracks
        """


        data = self._api_call(api_methods.ALBUM_TRACKS, params={
            "ALB_ID": album_id,
            "NB": -1
        })

        for i, track in enumerate(data["results"]["data"]):
            track["_POSITION"] = i + 1

        return data["results"]["data"]

    def get_artist(self, artist_id):
        """Gets the artist data from the given {artist_id}
        
        Arguments:
            artist_id {str} -- Artist Id
        
        Returns:
            dict -- Artist data
        """


        data = self._api_call(api_methods.PAGE_ARTIST, params={
            "ART_ID": artist_id,
            "LANG": "en"
        })

        return data["results"]

    def get_artist_poster(self, artist, size=500, ext="jpg"):
        """Gets the artist poster as a binary data
        
        Arguments:
            artist {dict} -- artist data
        
        Keyword Arguments:
            size {int} -- Size of the image, {size}x{size} (default: {500})
            ext {str} -- Extension of the image, can be ('.jpg' or '.png') (default: {"jpg"})
        
        Returns:
            bytes -- Binary data of the image
        """


        if "DATA" in artist:
            artist = artist["DATA"]

        return self._get_poster(artist["ART_PICTURE"], size=size, ext=ext)

    def get_artist_discography(self, artist_id):
        """Gets the artist's discography (tracks)
        
        Arguments:
            artist_id {str} -- Artist Id
        
        Returns:
            dict -- Artist discography data
        """


        data = self._api_call(api_methods.ARTIST_DISCOGRAPHY, params={
            "ART_ID": artist_id,
            "NB": 500,
            "NB_SONGS": -1,
            "START": 0
        })

        return data["results"]["data"]

    def get_artist_top_tracks(self, artist_id):
        """Gets the top tracks of the given artist
        
        Arguments:
            artist_id {str} -- Artist Id
        
        Returns:
            list -- List of track
        """


        data = self._api_call(api_methods.ARTIST_TOP_TRACKS, params={
            "ART_ID": artist_id,
            "NB": 100
        })

        for i, track in enumerate(data["results"]["data"]):
            track["_POSITION"] = i + 1

        return data["results"]["data"]

    def get_playlist(self, playlist_id):
        """Gets the playlist data from the given playlist_id
        
        Arguments:
            playlist_id {str} -- Playlist Id
        
        Returns:
            dict -- Playlist data
        """


        data = self._api_call(api_methods.PAGE_PLAYLIST, params={
            "playlist_id": playlist_id,
            "LANG": "en"
        })

        return data["results"]

    def get_playlist_tracks(self, playlist_id):
        """Gets the tracks inside the playlist
        
        Arguments:
            playlist_id {str} -- Playlist Id
        
        Returns:
            list -- List of tracks
        """


        data = self._api_call(api_methods.PLAYLIST_TRACKS, params={
            "PLAYLIST_ID": playlist_id,
            "NB": -1
        })

        for i, track in enumerate(data["results"]["data"]):
            track["_POSITION"] = i + 1

        return data["results"]["data"]

    def get_suggested_queries(self, query):
        """Gets suggestion based on the given {query}
        
        Arguments:
            query {str} -- Query keyword

        Returns:
            list -- List of suggestions
        """


        data = self._api_call(api_methods.GET_SUGGESTED_QUERIES, params={
            "QUERY": query
        })

        results = data["results"]["SUGGESTION"]
        for result in results:
            if "HIGHLIGHT" in result:
                del result["HIGHLIGHT"]

        return results

    def search_tracks(self, query, limit=30, index=0):
        """Searches tracks on a given query
        
        Arguments:
            query {str} -- Query keyword
        
        Keyword Arguments:
            limit {int} -- Number of results (default: {30})
            index {int} -- Offset (default: {0})
        
        Returns:
            list -- List of tracks
        """


        return self._legacy_search(api_methods.SEARCH_TRACK, query, limit=limit, index=index)

    def search_albums(self, query, limit=30, index=0):
        """Searches albums on a given query
        
        Arguments:
            query {str} -- Query keyword
        
        Keyword Arguments:
            limit {int} -- Number of results (default: {30})
            index {int} -- Offset (default: {0})
        
        Returns:
            list -- List of albums
        """


        return self._legacy_search(api_methods.SEARCH_ALBUM, query, limit=limit, index=index)

    def search_artists(self, query, limit=30, index=0):
        """Searches artists on a given query
        
        Arguments:
            query {str} -- Query keyword
        
        Keyword Arguments:
            limit {int} -- Number of tracks (default: {30})
            index {int} -- Offset (default: {0})
        
        Returns:
            list -- List of artists
        """

        return self._legacy_search(api_methods.SEARCH_ARTIST, query, limit=limit, index=index)

    def search_playlists(self, query, limit=30, index=0):
        """Searches playlists on a given query
        
        Arguments:
            query {str} -- Query keyword
        
        Keyword Arguments:
            limit {int} -- Number of tracks (default: {30})
            index {int} -- Offset (default: {0})
        
        Returns:
            list -- List of playlists
        """


        return self._legacy_search(api_methods.SEARCH_PLAYLIST, query, limit=limit, index=index)

    def _legacy_search(self, method, query, limit=30, index=0):
        query = util.clean_query(query)

        data = self._legacy_api_call(method, {
            "q": query,
            "limit": limit,
            "index": index
        })

        return data["data"]

    def _get_poster(self, poster_id, size=500, ext="jpg"):
        ext = ext.lower()
        if ext != "jpg" and ext != "png":
            raise ValueError("Image extension should only be jpg or png!")

        url = f'https://e-cdns-images.dzcdn.net/images/cover/{poster_id}/{size}x{size}.{ext}'
        return {
            "image": self.session.get(url, params=networking_settings.HTTP_HEADERS, cookies=self.get_cookies()).content,
            "size": (size, size),
            "ext": ext,
            "mime_type": "image/jpeg" if ext == "jpg" else "image/png"
        }

    def _write_mp3_tags(self, path, track, tags=None):
        if "DATA" in track:
            track = track["DATA"]

        if not tags:
            tags = self.get_track_tags(track)

        audio = MP3(path, ID3=EasyID3)
        audio.delete()
        EasyID3.RegisterTextKey("label", "TPUB")

        cover = tags["_albumart"]
        del tags["_albumart"]

        for key, val in tags.items():
            audio[key] = str(val)
        audio.save()

        cover_handle = ID3(path)
        cover_handle["APIC"] = APIC(
            type=3,
            mime=cover["mime_type"],
            data=cover["image"]
        )
        cover_handle.save(path)

        return True

    def _write_flac_tags(self, path, track, tags=None):
        if "DATA" in track:
            track = track["DATA"]

        if not tags:
            tags = self.get_track_tags(track)

        audio = File(path)
        audio.delete()

        pic = mutagen.flac.Picture()
        pic.data = tags["_albumart"]["image"]

        audio.clear_pictures()
        audio.add_picture(pic)
        
        del tags["_albumart"]

        for key, val in tags.items():
            audio[key] = str(val)
        audio.save()

        return True

    def _select_valid_quality(self, track, quality):
        # If the track does not support the desired quality or if the given quality is not in the TRACK_FORMAT_MAP,
        # Use the default quality
        valid_qualities = self.get_track_valid_quality(track)

        if not quality or not quality in valid_qualities:
            default_size = int(track["FILESIZE"])

            for key in track_formats.TRACK_FORMAT_MAP.keys():
                if f"FILESIZE_{key}" in track and int(track[f"FILESIZE_{key}"]) == default_size:
                    quality = track_formats.TRACK_FORMAT_MAP[key]
                    break
        else:
            quality = track_formats.TRACK_FORMAT_MAP[quality]

        return quality

    def _api_call(self, method, params={}):
        token = "null"
        if method != api_methods.GET_USER_DATA:
            token = self.token

        res = self.session.post(api_urls.API_URL, json=params, params={
            "api_version": "1.0",
            "api_token": token,
            "input": "3",
            "method": method
        }, headers=networking_settings.HTTP_HEADERS, cookies=self.get_cookies())

        data = res.json()

        if "error" in data and data["error"]:
            error_type = list(data["error"].keys())[0]
            error_message = data["error"][error_type]
            raise APIRequestError(
                "{0} : {1}".format(error_type, error_message))

        return data

    def _legacy_api_call(self, method, params={}):
        res = self.session.get("{0}/{1}".format(api_urls.LEGACY_API_URL, method),
                               params=params, headers=networking_settings.HTTP_HEADERS, cookies=self.get_cookies())

        data = res.json()

        if "error" in data and data["error"]:
            error_type = list(data["error"].keys())[0]
            error_message = data["error"][error_type]
            raise APIRequestError(
                "{0} : {1}".format(error_type, error_message))

        return data
