from rich.progress import (
    BarColumn,
    DownloadColumn,
    TextColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    Progress
)


class BaseProgressHandler:
    def __init__(self, *args, **kwargs):
        pass

    def initialize(self, iterable, track_title, track_quality, total_size, chunk_size, **kwargs):
        self.iterable = iterable
        self.track_title = track_title
        self.track_quality = track_quality
        self.total_size = total_size
        self.chunk_size = chunk_size
        self.size_downloaded = 0
        self.current_chunk_size = 0

    def update(self, *args, **kwargs):
        if "current_chunk_size" in kwargs:
            self.current_chunk_size = kwargs["current_chunk_size"]
            self.size_downloaded += self.current_chunk_size

    def close(self, *args, **kwargs):
        pass


class DefaultProgressHandler(BaseProgressHandler):
    def __init__(self):
        self.progress = Progress(
            TextColumn("[bold blue]{task.fields[title]}", justify="right"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
        )

    def initialize(self, *args, **kwargs):
        super().initialize(*args)

        self.download_task = self.progress.add_task(
            self.track_title, title=self.track_title, total=self.total_size)
        self.progress.start()

    def update(self, *args, **kwargs):
        super().update(**kwargs)
        self.progress.update(self.download_task,
                             advance=self.current_chunk_size)

    def close(self):
        self.progress.stop()
