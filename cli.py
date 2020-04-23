import click
from click import echo, types
from PyInquirer import prompt

from pydeezer import Deezer
from pydeezer.exceptions import LoginError
from pydeezer.constants.track_formats import MP3_128, MP3_256, MP3_320, FLAC

from validators import ArlValidator


@click.group()
def cli():
    """PyDeezer CLI"""


@cli.command()
@click.option("-a", "--arl", type=types.STRING, help="Used to be able to login to Deezer. Check the docs on how to get one.")
@click.option("--media-type", type=types.Choice(["Track", "Album", "Playlist", "Artist"], case_sensitive=False), help="Sets the media type and how it searches the api.")
@click.option("-d", "--download-dir", type=types.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True), help="Sets the directory on where the tracks are to be saved.")
@click.option("-q", "--quality", type=types.Choice([MP3_128, MP3_256, MP3_320, FLAC], case_sensitive=False), help="Sets the quality of the tracks. if the provided quality is not supported, the default quality of the track will be used.")
def download(arl, media_type, download_dir, quality):
    """Download tracks"""

    deezer = Deezer()

    if arl:
        user = deezer.login_via_arl(arl)
    else:
        def validate_arl(arl):
            try:
                deezer.login_via_arl(arl)
            except LoginError:
                return "Arl is invalid. Please try again..."
            return True

        user = prompt({
            "type": "input",
            "name": "user",
            "message": "Required: Please input your ARL.",
            "validate": validate_arl,
            "filter": lambda _: deezer.user
        })["user"]


if __name__ == "__main__":
    cli()
