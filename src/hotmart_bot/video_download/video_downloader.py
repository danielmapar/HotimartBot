import os

import youtube_dl
import youtube_dl.downloader.external

from hotmart_bot.models.course import Video
from hotmart_bot.downloader.hotmart import HotmartFD

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"


# inject the new downloader in YTDL lib
youtube_dl.downloader.external._BY_NAME['hotmart'] = HotmartFD

class VideoDownloader(object):
    @staticmethod
    def download_video(video: Video, folder: str, referer: str):
        print("URL: ", video.url)
        youtube_dl.utils.std_headers["Referer"] = referer
        
        if video.cookies:
            youtube_dl.utils.std_headers['Cookie'] = video.cookies

        ydl_opts = {
            "outtmpl": os.path.join(folder, "%(title)s.%(ext)s"),
            "quiet": True,
            "verbose": False,
            "format": "best",
            "fragment_retries": 10,
            "http_headers": {
                'Origin': referer,
                'Referer': referer,
                'Cookie': video.cookies
            }
        }

        # we need some headers to bypass CloudFront checker
        if video.source == 'hotmart':
            youtube_dl.utils.std_headers['User-Agent'] = DEFAULT_USER_AGENT
            ydl_opts['external_downloader'] = 'hotmart'

        
        
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video.url])
