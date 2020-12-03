import os
from typing import List

import pathvalidate
from selenium.webdriver.remote.webelement import WebElement


class Module:
    @classmethod
    def from_webelement(cls, element: WebElement):
        id = element.find_element_by_class_name("navigation-module-index").text
        name = element.find_element_by_class_name("navigation-module-title").text

        module_name = "".join([id, "-", name])

        return cls(module_name, element, [])

    def __init__(self, name: str, element: WebElement, lessons: List = []) -> None:
        self.name = name
        self.element = element
        self.lessons = lessons
        self.lessons_elements = []
        self.path = ""

    def create_folder(self, course_path: str = None):
        sanitized_folder_name = pathvalidate.sanitize_filename(self.name)
        if course_path:
            folder_path = os.path.join(
                os.path.abspath(course_path), sanitized_folder_name
            )
        else:
            folder_path = os.path.join(os.getcwd(), sanitized_folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        self.path = folder_path
