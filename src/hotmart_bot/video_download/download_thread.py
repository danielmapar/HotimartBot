from threading import Thread
from typing import Any, List

from hotmart_bot.models.course import Video
from hotmart_bot.video_download.video_downloader import VideoDownloader


class DownloadThread(Thread):
    def __init__(
        self,
        parent: Any = None,
        videos: List[Video] = None,
        folder: str = None,
        referer: str = None,
    ):
        self.parent = parent
        self.videos = videos
        self.folder = folder
        self._referer = referer
        super(DownloadThread, self).__init__()

    def run(self):
        print(
            "In progess: "
            + str(self.parent.THREADS_DONE + 1)
            + "/"
            + str(self.parent.TOTAL_THREADS)
        )
        for video in self.videos:
            done = None
            retry = 0
            while done is None:
                if retry == 5:
                    done = True
                try:
                    VideoDownloader.download_video(video, self.folder, self._referer)
                    done = True
                except:
                    retry = retry + 1
        self.parent and self.parent.on_thread_finished()
