from os import path

import click
from click import echo, types
from PyInquirer import prompt

from . import Deezer, util
from .exceptions import LoginError
from .constants.track_formats import FORMAT_LIST


@click.group()
def cli():
    """PyDeezer CLI"""


@cli.command()
@click.option("-a", "--arl", type=types.STRING, help="Used to be able to login to Deezer. Check the docs on how to get one.")
@click.option("--media-type", type=types.Choice(["Track", "Album", "Playlist", "Artist"], case_sensitive=False), help="Sets the media type and how it searches the api.")
@click.option("-d", "--download-dir", type=types.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True), help="Sets the directory on where the tracks are to be saved.")
@click.option("-q", "--quality", type=types.Choice(FORMAT_LIST, case_sensitive=False), help="Sets the quality of the tracks. if the provided quality is not supported, the default quality of the track will be used.")
def download(arl, media_type, download_dir, quality):
    """Download tracks"""

    deezer = Deezer()
    user = None

    if arl:
        try:
            user = deezer.login_via_arl(arl)
        except LoginError:
            user = None
            echo("The Arl you supplied is invalid. Please try again...")

    if not user:
        def validate_arl(arl):
            try:
                deezer.login_via_arl(arl)
            except LoginError:
                return "Arl is invalid. Please try again..."
            return True

        user = prompt({
            "type": "input",
            "name": "user",
            "message": "Please input your ARL.",
            "validate": validate_arl,
            "filter": lambda _: deezer.user
        })["user"]

    def search_choices(answers):
        query = answers["query"]

        if "media_type" in answers:
            _media_type = answers["media_type"]
        else:
            _media_type = media_type

        _media_type = _media_type.upper()

        if _media_type == "ALBUM":
            return [{
                "name": album["title"] + " - " + album["artist"]["name"],
                "value": album["id"],
                "short": album["title"]
            } for album in deezer.search_albums(query)]
        elif _media_type == "PLAYLIST":
            return [{
                "name": playlist["title"] + " - " + playlist["user"]["name"],
                "value": playlist["id"],
                "short": playlist["title"]
            } for playlist in deezer.search_playlists(query)]
        elif _media_type == "ARTIST":
            return [{
                "name": artist["name"],
                "value": artist["id"],
                "short": artist["name"]
            } for artist in deezer.search_artists(query)]

    def track_choices(answers):
        if "media_type" in answers:
            _media_type = answers["media_type"]
        else:
            _media_type = media_type

        _media_type = _media_type.upper()

        if _media_type == "ALBUM":
            album_id = answers["album"]

            return [{
                "name": track["TRACK_NUMBER"] + " - " + track["SNG_TITLE"],
                "value": track["SNG_ID"],
                "short": track["SNG_TITLE"]
            } for track in deezer.get_album_tracks(album_id)]
        elif _media_type == "PLAYLIST":
            playlist_id = answers["playlist"]

            return [{
                "name": track["SNG_TITLE"] + " - " + track["ALB_TITLE"] + " - " + track["ART_NAME"],
                "value": track["SNG_ID"],
                "short": track["SNG_TITLE"]
            } for track in deezer.get_playlist_tracks(playlist_id)]
        elif _media_type == "ARTIST":
            artist_id = answers["artist"]

            return [{
                "name": track["SNG_TITLE"] + " - " + track["ALB_TITLE"],
                "value": track["SNG_ID"],
                "short": track["SNG_TITLE"]
            } for track in deezer.get_artist_top_tracks(artist_id)]
        else:
            query = answers["query"]

            return [{
                "name": track["title"] + " - " + track["artist"]["name"],
                "value": track["id"],
                "short": track["title_short"]
            } for track in deezer.search_tracks(query)]

    questions = [
        {
            "type": "list",
            "name": "media_type",
            "message": "How do you want to search?",
            "when": lambda _: not media_type,
            "choices": ["By Track", "By Album", "By Playlist", "By Artist"],
            "filter": lambda mt: mt[3:]
        },
        {
            "type": "input",
            "name": "query",
            "message": "Input a search query.",
            "validate": lambda q: len(q) > 0
        },
        {
            "type": "list",
            "name": "album",
            "message": "Select an album.",
            "when": lambda answers: ("media_type" in answers and answers["media_type"] == "Album") or media_type == "Album",
            "choices": search_choices
        },
        {
            "type": "list",
            "name": "playlist",
            "message": "Select a playlist.",
            "when": lambda answers: ("media_type" in answers and answers["media_type"] == "Playlist") or media_type == "Playlist",
            "choices": search_choices
        },
        {
            "type": "list",
            "name": "artist",
            "message": "Select an artist.",
            "when": lambda answers: ("media_type" in answers and answers["media_type"] == "Artist") or media_type == "Artist",
            "choices": search_choices
        },
        {
            "type": "checkbox",
            "name": "tracks",
            "message": "Select track(s) to be downloaded.",
            "choices": track_choices
        },
        {
            "type": "list",
            "name": "quality",
            "message": "Select track quality. MP3 320 is recommended.",
            "when": lambda _: not quality,
            "choices": FORMAT_LIST
        },
        {
            "type": "input",
            "name": "download_dir",
            "message": "Specify a valid download directory.",
            "when": lambda _: not download_dir
        }
    ]

    answers = prompt(questions)

    tracks = answers["tracks"]
    quality = quality if quality else answers["quality"]
    download_dir = download_dir if download_dir else answers["download_dir"]

    echo(f"Starting download of {len(tracks)} tracks.")

    for track in tracks:
        t = deezer.get_track(track)
        info = t["info"]["DATA"]

        artist_name = util.clean_filename(info["ART_NAME"])
        album_name = util.clean_filename(info["ALB_TITLE"])

        download_path = path.join(download_dir, artist_name, album_name)
        util.create_folders(download_path)

        t["download"](download_path, quality=quality)

    echo("Done!")


if __name__ == "__main__":
    cli()
