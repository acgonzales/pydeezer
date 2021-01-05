from tqdm import tqdm


class BaseProgressHandler:
    def __init__(self, *args, **kwargs):
        pass

    def initialize(self, iterable, track_title, track_quality, total_size, chunk_size):
        self.iterable = iterable
        self.track_title = track_title
        self.track_quality = track_quality
        self.total_size = total_size
        self.chunk_size = chunk_size
        self.size_downloaded = 0
        self.current_chunk_size = 0

    def update(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


class DefaultProgressHandler(BaseProgressHandler):
    def __init__(self, position=0):
        self.position = position

    def initialize(self, *args):
        super().initialize(*args)

        self.pbar = tqdm(self.iterable, total=self.total_size, position=self.position,
                         unit="B", unit_scale=True, unit_divisor=1024, leave=False, desc=self.track_title)

    def update(self):
        self.pbar.update(self.current_chunk_size)

    def close(self):
        self.pbar.close()
