import os

import youtube_dl


class VideoDownloader(object):
    @staticmethod
    def download_video(url: str, folder: str, referer: str):
        print("URL: ", url)
        youtube_dl.utils.std_headers["Referer"] = referer
        ydl_opts = {
            "outtmpl": os.path.join(folder, "%(title)s.%(ext)s"),
            "quiet": True,
            "format": "best",
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
