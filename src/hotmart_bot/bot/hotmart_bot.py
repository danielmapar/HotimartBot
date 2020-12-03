import time
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys

from hotmart_bot.models.course import Lesson, Module, Video
from hotmart_bot.video_download.download_manager import DownloadManager


class HotmartBot(object):
    def __init__(self, driver: WebDriver) -> None:
        self._driver = driver

    def _extract_video_urls(self) -> List[Video]:
        videos = []
        iframes = self._driver.find_elements_by_tag_name("iframe")
        for iframe in iframes:
            src = iframe.get_attribute("src")
            if "youtube" in src:
                videos.append(Video("youtube", src))
            elif "vimeo" in src:
                videos.append(Video("vimeo", src))
        return videos

    def login(self, domain: str, username: str, pwd: str) -> None:
        URL = "".join(["https://", domain, ".club.hotmart.com"])
        self._driver.get(URL)
        login = self._driver.find_element_by_name("login")
        login.clear()
        login.send_keys(username)

        password = self._driver.find_element_by_name("password")
        password.clear()
        password.send_keys(pwd)
        password.send_keys(Keys.RETURN)

    def get_modules_list(self) -> List[Module]:
        modules = []

        modules_elements = self._driver.find_element_by_id(
            "navigation-modules"
        ).find_elements_by_class_name("card")

        for module_element in modules_elements:
            time.sleep(2)
            module_element.click()
            course_module = Module.from_webelement(module_element)
            modules.append(course_module)
        return modules

    def get_lessons_list(self, module: Module) -> List[Lesson]:
        lessons = []
        lessons_elements = module.element.find_element_by_class_name(
            "navigation-module-pages"
        ).find_elements_by_class_name("navigation-page")
        for lesson_element in lessons_elements:

            lesson_element.find_element_by_class_name(
                "navigation-page-info"
            ).find_element_by_class_name("navigation-page-title")
            lesson_element.click()
            time.sleep(2)
            videos = self._extract_video_urls()
            lesson = Lesson(
                lesson_element.text,
                lesson_element,
                [],
                self._driver.current_url,
                videos,
            )
            lessons.append(lesson)

        return lessons
