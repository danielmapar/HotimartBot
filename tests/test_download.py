import pytest
import argparse
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

from hotmart_bot.bot.hotmart_bot import HotmartBot
from hotmart_bot.video_download.download_manager import DownloadManager
from hotmart_bot.__main__ import main, create_parser, create_webdriver


def test_download():
    parser = create_parser()
    args = parser.parse_args(['your_course_here', '-ef'])

    SITE = args.site
    if args.envfile:
        USERNAME = os.getenv("ACCOUNT_USERNAME")
        PWD = os.getenv("PASSWORD")
    else:
        USERNAME = args.username
        PWD = args.password

    driver = create_webdriver()
    hb = HotmartBot(driver)

    hb.login(SITE, USERNAME, PWD)
    modules = hb.get_modules_list()
    download_manager = DownloadManager(len(modules))

    for module in modules:
        module.lessons = hb.get_lessons_list(module)
        if args.output_path:
            module.create_folder(args.output_path)
        else:
            module.create_folder()
            
        for lesson in module.lessons:
            lesson.create_folder(module)
            download_manager.new_thread(lesson.videos, lesson.path, SITE).start()
