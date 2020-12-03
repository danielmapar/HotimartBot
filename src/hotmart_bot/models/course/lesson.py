import os
from typing import List, Tuple

import pathvalidate
from hotmart_bot.models.course.module import Module
from selenium.webdriver.remote.webelement import WebElement


class Lesson(object):
    def __init__(
        self,
        name: str,
        element: WebElement,
        attachments: List,
        url: str,
        videos: List[Tuple[str, str]],
    ) -> None:
        self.name = name
        self.element = element
        self.attachments = attachments
        self.url = url
        self.videos = videos
        self.path = ""

    def create_folder(self, parent_module: Module) -> None:
        sanitized_folder_name = pathvalidate.sanitize_filename(self.name)
        folder_path = os.path.join(parent_module.path, sanitized_folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        self.path = folder_path
