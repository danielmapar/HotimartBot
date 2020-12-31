import json
import re
import time

from http.cookies import SimpleCookie

from typing import List

from seleniumwire import webdriver

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys

from webdriver_manager.chrome import ChromeDriverManager

from hotmart_bot.models.course import Lesson, Module, Video
from hotmart_bot.video_download.video_downloader import VideoDownloader


request_history = []

def callback_requests(req, req_body, res, res_body):
    request_history.append((req, res))


class HotmartBot(object):
    def __init__(self) -> None:
        self._create_webdriver()


    def _create_webdriver(self):
        options = ChromeOptions()
        options.add_argument("--start-maximized")

        capabilities = DesiredCapabilities.CHROME
        capabilities["goog:loggingPrefs"] = {"performance": "ALL"}

        soptions = {
            'custom_response_handler': callback_requests
        }

        self._driver = webdriver.Chrome(ChromeDriverManager().install(), options=options, desired_capabilities=capabilities, seleniumwire_options=soptions)
        self._driver.set_page_load_timeout(60 * 5)
        self._driver.implicitly_wait(10)


    def _extract_video_urls(self):
        videos = []
        iframes = self._driver.find_elements_by_tag_name("iframe")
        for iframe in iframes:
            src = iframe.get_attribute("src")
            if "youtube" in src:
                yield Video("youtube", src)
            elif "vimeo" in src:
                yield Video("vimeo", src)
            elif "player.hotmart" in src:
                src = self.discover_url()
                cookies = self.get_cookies(src)
                yield Video("hotmart", src, cookies)


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
        
        lessons_elements = module.element.find_element_by_class_name(
            "navigation-module-pages"
        ).find_elements_by_class_name("navigation-page")
        
        for lesson_element in lessons_elements:

            lesson_element.find_element_by_class_name(
                "navigation-page-info"
            ).find_element_by_class_name("navigation-page-title")
            lesson_element.click()
            time.sleep(2)

            lesson = Lesson(
                lesson_element.text,
                lesson_element,
                [],
                self._driver.current_url,
                [],
            )

            lesson.create_folder(module)

            for video in self._extract_video_urls():
                VideoDownloader.download_video(video, lesson.path, 'https://player.hotmart.com/')

    @staticmethod
    def filter_request(request):
        video_regex = re.compile('^https://player.hotmart.com/embed/[^/]+/source/[^/]+=\\.m3u8$')

        try:
            url = request[0].path
            return video_regex.match(url)
        except KeyError:
            return False

        return False

    @staticmethod
    def filter_token(request):
        video_regex = re.compile('^https://player.hotmart.com/embed/[^/]+?token=.*$')

        try:
            url = request[0].path
            return video_regex.match(url)
        except KeyError:
            return False

        return False

    def discover_url(self):

        video_requests = list(filter(HotmartBot.filter_request, request_history))

        if len(video_requests) > 0:
            return video_requests[-1][0].path

        return None

    def get_cookies(self, video_url):
        video_id_regex = re.compile('^https://player.hotmart.com/embed/([^/]+)/source/[^/]+=\\.m3u8$')
        video_id = ''

        match = video_id_regex.match(video_url)
        if match:
            video_id = match.group(1)

        video_requests = list(filter(lambda x:x[0].path == video_url, request_history))

        cookies = ''

        if len(video_requests) > 0:
            headers = video_requests[-1][0].headers
            cookies = headers.get('Cookie')

        token_requests = list(filter(HotmartBot.filter_token, request_history))

        if len(token_requests) == 0:
            return cookies
            
        video_cookies = []

        for request in token_requests:
            simple_cookie = SimpleCookie()
            
            headers = request[1].headers
            raw_cookies = headers.get_all('Set-Cookie')
        
            for c in raw_cookies:
                simple_cookie.load(c)

            for entry in simple_cookie.keys():
                path = simple_cookie[entry]['path']
                if video_id in path:
                    video_cookies.append(entry + '=' + simple_cookie[entry].coded_value)

        if len(video_cookies) > 0:
            video_cookies = list(set(video_cookies))
            cookies = cookies.strip().strip(';')
            cookies = cookies + '; ' + "; ".join(video_cookies)

        return cookies
