from typing import Type
from concurrent.futures import ThreadPoolExecutor, as_completed

import rich
from rich.progress import (
    BarColumn,
    DownloadColumn,
    TextColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    Progress
)

from pydeezer.ProgressHandler import BaseProgressHandler, DefaultProgressHandler
from pydeezer.constants import track_formats


class Downloader:
    class ProgressHandler(BaseProgressHandler):
        def __init__(self):
            self.tracks = {}
            self.progress = Progress(
                TextColumn("[bold blue]{task.fields[title]}", justify="left"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.2f}%",
                "•",
                DownloadColumn(),
                "•",
                TransferSpeedColumn(),
                "•",
                TimeRemainingColumn(),
                transient=True
            )

        def initialize(self, iterable, track_title, track_quality, total_size, chunk_size, **kwargs):
            track_id = kwargs["track_id"]

            task = self.progress.add_task(
                track_title, title=track_title, total=total_size)

            self.progress.console.print(
                f"[bold red]{track_title}[/] has started downloading.")

            self.tracks[track_id] = {
                "id": track_id,
                "iterable": iterable,
                "title": track_title,
                "quality": track_quality,
                "total_size": total_size,
                "chunk_size": chunk_size,
                "task": task,
                "size_downloaded": 0,
                "current_chunk_size": 0
            }

            self.progress.start()

        def update(self, *args, **kwargs):
            track = self.tracks[kwargs["track_id"]]
            track["current_chunk_size"] = kwargs["current_chunk_size"]
            track["size_downloaded"] += track["current_chunk_size"]

            self.progress.update(track["task"],
                                 advance=track["current_chunk_size"])

        def close(self, *args, **kwargs):
            track = self.tracks[kwargs["track_id"]]
            track_title = track["title"]
            self.progress.print(
                f"[bold red]{track_title}[/] is done downloading.")

        def close_progress(self):
            self.progress.refresh()
            self.progress.stop()

    def __init__(self, deezer, track_ids_to_download, download_dir, quality=track_formats.MP3_320,
                 concurrent_downloads=2, progress_handler: Type[BaseProgressHandler] = None):
        self.deezer = deezer
        self.track_ids = track_ids_to_download
        self.download_dir = download_dir
        self.workers = concurrent_downloads
        self.quality = quality

        if not progress_handler:
            progress_handler = self.ProgressHandler()

        self.progress_handler = progress_handler

    def start(self):
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            pool.map(self._download, self.track_ids)

        rich.print(
            f"[bold green]Done downloading all {len(self.progress_handler.tracks)} tracks.")
        self.progress_handler.close_progress()

    def _download(self, track_id):
        track = self.deezer.get_track(track_id)
        track["download"](self.download_dir, quality=self.quality, show_messages=False,
                          progress_handler=self.progress_handler)
