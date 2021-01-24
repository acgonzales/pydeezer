from functools import partial
import hashlib
from os import path

from deezer import Deezer as DeezerPy
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import mutagen
from mutagen import File
from mutagen.id3 import ID3, APIC
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3


from .ProgressHandler import BaseProgressHandler, DefaultProgressHandler

from .constants import track_formats

from .exceptions import LoginError
from .exceptions import APIRequestError
from .exceptions import DownloadLinkDecryptionError

from . import util


class Deezer(DeezerPy):
    def __init__(self, arl=None):
        """Instantiates a Deezer object

        Keyword Arguments:
            arl {str} -- Login using the given arl (default: {None})
        """
        super().__init__()

        if arl:
            self.arl = arl
            self.login_via_arl(arl)

    def login_via_arl(self, arl, child=0):
        """Logs in to Deezer using the given

        Arguments:
            arl {[type]} -- [description]

        Returns:
            dict -- User data given by the Deezer API
        """
        super().login_via_arl(arl, child=child)
        return self.current_user

    @property
    def user(self):
        return self.current_user

    def get_track(self, track_id):
        """Gets the track info using the Deezer API

        Arguments:
            track_id {str} -- Track Id

        Returns:
            dict -- Dictionary that contains the {info}, {download} partial function, {tags}, and {get_tag} partial function.
        """

        data = self.gw.get_track(track_id)

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

        track = track["DATA"] if "DATA" in track else track

        qualities = []

        # Fixes issue #4
        for key in [track_formats.MP3_128, track_formats.MP3_320, track_formats.FLAC]:
            download_url = self.get_track_download_url(
                track, quality=key, fallback=False)

            res = self.session.get(
                download_url, stream=True)

            if res.status_code == 200 and int(res.headers["Content-length"]) > 0:
                qualities.append(key)

        # Gonna comment these out in case Deezer decides to fix it themselves.
        # for key in track_formats.TRACK_FORMAT_MAP:
        #     k = f"FILESIZE_{key}"
        #     if k in track:
        #         if str(track[k]) != "0":
        #             qualities.append(key)

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

        track = track["DATA"] if "DATA" in track else track

        album_data = self.get_album(track["ALB_ID"])

        if "main_artist" in track["SNG_CONTRIBUTORS"]:
            main_artists = track["SNG_CONTRIBUTORS"]["main_artist"]
            artists = main_artists[0]
            for i in range(1, len(main_artists)):
                artists += separator + main_artists[i]
        else:
            artists = track.get("ART_NAME")

        title = track.get("SNG_TITLE")

        if "VERSION" in track and track["VERSION"] != "":
            title += " " + track["VERSION"]

        def should_include_featuring():
            # Checks if the track title already have the featuring artists in its title
            feat_keywords = ["feat.", "featuring", "ft."]

            for keyword in feat_keywords:
                if keyword in title.lower():
                    return False
            return True

        if should_include_featuring() and "featuring" in track["SNG_CONTRIBUTORS"]:
            featuring_artists_data = track["SNG_CONTRIBUTORS"]["featuring"]
            featuring_artists = featuring_artists_data[0]
            for i in range(1, len(featuring_artists_data)):
                featuring_artists += separator + featuring_artists_data[i]

            title += f" (feat. {featuring_artists})"

        total_tracks = album_data["nb_tracks"]
        track_number = str(track["TRACK_NUMBER"]) + "/" + str(total_tracks)

        cover = self.get_album_poster(album_data, size=1000)

        tags = {
            "title": title,
            "artist": artists,
            "genre": None,
            "album": track.get("ALB_TITLE"),
            "albumartist": track.get("ART_NAME"),
            "label": album_data.get("label"),
            "date": track.get("PHYSICAL_RELEASE_DATE"),
            "discnumber": track.get("DISK_NUMBER"),
            "tracknumber": track_number,
            "isrc": track.get("ISRC"),
            "copyright": track.get("COPYRIGHT"),
            "_albumart": cover,
        }

        if len(album_data["genres"]["data"]) > 0:
            tags["genre"] = album_data["genres"]["data"][0]["name"]

        if "author" in track["SNG_CONTRIBUTORS"]:
            _authors = track["SNG_CONTRIBUTORS"]["author"]

            authors = _authors[0]
            for i in range(1, len(_authors)):
                authors += separator + _authors[i]

            tags["author"] = authors

        return tags

    def get_track_download_url(self, track, quality=None, fallback=True, renew=False, **kwargs):
        """Gets and decrypts the download url of the given track in the given quality

        Arguments:
            track {dict} -- Track dictionary, similar to the {info} value that is returned {using get_track()}

        Keyword Arguments:
            quality {str} -- Use values from {constants.track_formats}, will get the default quality if None or an invalid is given. (default: {None})
            fallback {bool} -- Set to True to if you want to use fallback qualities when the given quality is not available. (default: {False})
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

        if not quality:
            quality = track_formats.MP3_128
            fallback = True

        try:
            # Just in case they passed in the whole dictionary from get_track()
            track = track["DATA"] if "DATA" in track else track

            if not "MD5_ORIGIN" in track:
                raise DownloadLinkDecryptionError(
                    "MD5 is needed to decrypt the download link.")

            md5_origin = track["MD5_ORIGIN"]
            track_id = track["SNG_ID"]
            media_version = track["MEDIA_VERSION"]
        except ValueError:
            raise ValueError(
                "You have passed an invalid argument. This method needs the \"DATA\" value in the dictionary returned by the get_track() method.")

        def decrypt_url(quality_code):
            magic_char = "¤"
            step1 = magic_char.join((md5_origin,
                                     str(quality_code),
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

        url = decrypt_url(track_formats.TRACK_FORMAT_MAP[quality]["code"])
        res = self.session.get(url, stream=True)

        if not fallback or (res.status_code == 200 and int(res.headers["Content-length"]) > 0):
            res.close()
            return (url, quality)
        else:
            if "fallback_qualities" in kwargs:
                fallback_qualities = kwargs["fallback_qualities"]
            else:
                fallback_qualities = track_formats.FALLBACK_QUALITIES

            for key in fallback_qualities:
                url = decrypt_url(
                    track_formats.TRACK_FORMAT_MAP[key]["code"])

                res = self.session.get(
                    url, stream=True)

                if res.status_code == 200 and int(res.headers["Content-length"]) > 0:
                    res.close()
                    return (url, key)

    def download_track(self, track, download_dir, quality=None, fallback=True, filename=None, renew=False,
                       with_metadata=True, with_lyrics=True, tag_separator=", ", show_messages=True,
                       progress_handler: BaseProgressHandler = None, **kwargs):
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
                        lyric_data = self.get_track_lyrics(
                            track["DATA"]["SNG_ID"])["info"]
                    else:
                        lyric_data = self.get_track_lyrics(
                            track["SNG_ID"])["info"]
                except APIRequestError:
                    with_lyrics = False

        track = track["DATA"] if "DATA" in track else track

        tags = self.get_track_tags(track, separator=tag_separator)

        url, quality_key = self.get_track_download_url(
            track, quality, fallback=fallback, renew=renew, **kwargs)
        blowfish_key = util.get_blowfish_key(track["SNG_ID"])

        # quality = self._select_valid_quality(track, quality)

        quality = track_formats.TRACK_FORMAT_MAP[quality_key]

        title = tags["title"]
        ext = quality["ext"]

        if not filename:
            filename = title + ext

        if not str(filename).endswith(ext):
            filename += ext

        filename = util.clean_filename(filename)

        download_dir = path.normpath(download_dir)
        download_path = path.join(download_dir, filename)

        util.create_folders(download_dir)

        if show_messages:
            print("Starting download of:", title)

        res = self.session.get(url, stream=True)
        chunk_size = 2048
        total_filesize = int(res.headers["Content-Length"])
        i = 0

        data_iter = res.iter_content(chunk_size)

        if not progress_handler:
            progress_handler = DefaultProgressHandler()

        progress_handler.initialize(data_iter, title, quality_key, total_filesize,
                                    chunk_size, track_id=track["SNG_ID"])

        with open(download_path, "wb") as f:
            f.seek(0)

            for chunk in data_iter:
                current_chunk_size = len(chunk)

                if i % 3 > 0:
                    f.write(chunk)
                elif len(chunk) < chunk_size:
                    f.write(chunk)
                    progress_handler.update(
                        track_id=track["SNG_ID"], current_chunk_size=current_chunk_size)
                    break
                else:
                    cipher = Cipher(algorithms.Blowfish(blowfish_key),
                                    modes.CBC(
                                        bytes([i for i in range(8)])),
                                    default_backend())

                    decryptor = cipher.decryptor()
                    dec_data = decryptor.update(
                        chunk) + decryptor.finalize()
                    f.write(dec_data)

                    current_chunk_size = len(dec_data)

                i += 1

                progress_handler.update(
                    track_id=track["SNG_ID"], current_chunk_size=current_chunk_size)

        if with_metadata:
            if ext.lower() == ".flac":
                self._write_flac_tags(download_path, track, tags=tags)
            else:
                self._write_mp3_tags(download_path, track, tags=tags)

        if with_lyrics:
            lyrics_path = path.join(download_dir, filename[:-len(ext)])
            self.save_lyrics(lyric_data, lyrics_path)

        if show_messages:
            print("Track downloaded to:", download_path)

        progress_handler.close(
            track_id=track["SNG_ID"], total_filesize=total_filesize)

    def get_tracks(self, track_ids):
        """Gets the list of the tracks that corresponds with the given {track_ids}

        Arguments:
            track_ids {list} -- List of track id

        Returns:
            list -- List of tracks
        """
        return self.gw.get_tracks_gw(track_ids)

    def get_track_lyrics(self, track_id):
        """Gets the lyrics data of the given {track_id}

        Arguments:
            track_id {str} -- Track Id

        Returns:
            dict -- Dictionary that containts the {info}, and {save} partial function.
        """

        data = self.gw.get_track_lyrics(track_id)

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

        filename = path.basename(save_path)
        filename = util.clean_filename(filename)
        save_path = path.join(path.dirname(save_path), filename)

        if not str(save_path).endswith(".lrc"):
            save_path += ".lrc"

        util.create_folders(path.dirname(save_path))

        with open(save_path, "w", encoding="utf-8") as f:
            if not "LYRICS_SYNC_JSON" in lyric_data:
                return False

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
        data = self.api.get_album(album_id)

        # TODO: maybe better logic?
        data["cover_id"] = str(data["cover_small"]).split(
            "cover/")[1].split("/")[0]

        return data

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

        # return self._get_poster(album["ALB_PICTURE"], size=size, ext=ext)
        return self._get_poster(album["cover_id"], size=size, ext=ext)

    def get_album_tracks(self, album_id):
        """Gets the tracks of the given {album_id}

        Arguments:
            album_id {str} -- Album Id

        Returns:
            list -- List of tracks
        """

        return self.gw.get_album_tracks(album_id)

    def get_artist(self, artist_id):
        """Gets the artist data from the given {artist_id}

        Arguments:
            artist_id {str} -- Artist Id

        Returns:
            dict -- Artist data
        """

        return self.gw.get_artist(artist_id)

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

        if not "ART_PICTURE" in artist and "DATA" in artist:
            artist = artist["DATA"]

        return self._get_poster(artist["ART_PICTURE"], size=size, ext=ext)

    def get_artist_discography(self, artist_id, **kwargs):
        """Gets the artist's discography (tracks)

        Arguments:
            artist_id {str} -- Artist Id

        Returns:
            dict -- Artist discography data
        """
        return self.gw.get_artist_discography(artist_id, **kwargs)

    def get_artist_top_tracks(self, artist_id, **kwargs):
        """Gets the top tracks of the given artist

        Arguments:
            artist_id {str} -- Artist Id

        Returns:
            list -- List of track
        """
        return self.gw.get_artist_top_tracks(artist_id, **kwargs)

    def get_playlist(self, playlist_id):
        """Gets the playlist data from the given playlist_id

        Arguments:
            playlist_id {str} -- Playlist Id

        Returns:
            dict -- Playlist data
        """
        return self.gw.get_playlist(playlist_id)

    def get_playlist_tracks(self, playlist_id):
        """Gets the tracks inside the playlist

        Arguments:
            playlist_id {str} -- Playlist Id

        Returns:
            list -- List of tracks
        """
        return self.gw.get_playlist_tracks(playlist_id)

    def get_suggested_queries(self, query):
        """Gets suggestion based on the given {query}

        Arguments:
            query {str} -- Query keyword

        Returns:
            list -- List of suggestions
        """

        data = self.gw.api_call("search_getSuggestedQueries", params={
            "QUERY": query
        })

        results = data["SUGGESTION"]
        for result in results:
            if "HIGHLIGHT" in result:
                del result["HIGHLIGHT"]

        return results

    def search_tracks(self, query, **kwargs):
        """Searches tracks on a given query

        Arguments:
            query {str} -- Query keyword

        Keyword Arguments:
            limit {int} -- Number of results (default: {30})
            index {int} -- Offset (default: {0})

        Returns:
            list -- List of tracks
        """
        return self.api.search_track(query, **kwargs)

    def search_albums(self, query, **kwargs):
        """Searches albums on a given query

        Arguments:
            query {str} -- Query keyword

        Keyword Arguments:
            limit {int} -- Number of results (default: {30})
            index {int} -- Offset (default: {0})

        Returns:
            list -- List of albums
        """
        return self.api.search_album(query, **kwargs)

    def search_artists(self, query, **kwargs):
        """Searches artists on a given query

        Arguments:
            query {str} -- Query keyword

        Keyword Arguments:
            limit {int} -- Number of tracks (default: {30})
            index {int} -- Offset (default: {0})

        Returns:
            list -- List of artists
        """

        return self.api.search_artist(query, **kwargs)

    def search_playlists(self, query, **kwargs):
        """Searches playlists on a given query

        Arguments:
            query {str} -- Query keyword

        Keyword Arguments:
            limit {int} -- Number of tracks (default: {30})
            index {int} -- Offset (default: {0})

        Returns:
            list -- List of playlists
        """

        return self.api.search_playlist(query, **kwargs)

    def _get_poster(self, poster_id, size=500, ext="jpg"):
        ext = ext.lower()
        if ext != "jpg" and ext != "png":
            raise ValueError("Image extension should only be jpg or png!")

        url = f'https://e-cdns-images.dzcdn.net/images/cover/{poster_id}/{size}x{size}.{ext}'

        return {
            "image": self.session.get(url).content,
            "size": (size, size),
            "ext": ext,
            "mime_type": "image/jpeg" if ext == "jpg" else "image/png"
        }

    def _write_mp3_tags(self, path, track, tags=None):
        track = track["DATA"] if "DATA" in track else track

        if not tags:
            tags = self.get_track_tags(track)

        audio = MP3(path, ID3=EasyID3)
        audio.delete()
        EasyID3.RegisterTextKey("label", "TPUB")

        cover = tags["_albumart"]
        del tags["_albumart"]

        for key, val in tags.items():
            if val:
                audio[key] = str(val)
        audio.save()

        if cover:
            cover_handle = ID3(path)
            cover_handle["APIC"] = APIC(
                type=3,
                mime=cover["mime_type"],
                data=cover["image"]
            )
            cover_handle.save(path)

        return True

    def _write_flac_tags(self, path, track, tags=None):
        track = track["DATA"] if "DATA" in track else track

        if not tags:
            tags = self.get_track_tags(track)

        audio = File(path)
        audio.delete()

        cover = tags["_albumart"]
        del tags["_albumart"]

        if cover:
            pic = mutagen.flac.Picture()
            pic.data = cover["image"]

            audio.clear_pictures()
            audio.add_picture(pic)

        for key, val in tags.items():
            if val:
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
