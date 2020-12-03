from typing import List

from .download_thread import DownloadThread


class DownloadManager(object):
    def __init__(self, total_pages: int = None):
        self.TOTAL_THREADS = total_pages
        self.THREADS_DONE = 0

    def new_thread(self, videos: List, folder: str, referer: str):
        return DownloadThread(
            parent=self, videos=videos, folder=folder, referer=referer
        )

    def on_thread_finished(self):
        self.THREADS_DONE = self.THREADS_DONE + 1
        print("Done: " + str(self.THREADS_DONE + 1) + "/" + str(self.TOTAL_THREADS))
