import os
import time
import shutil
import sys
from threading import Thread

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from pytube import YouTube

if (len(sys.argv) < 4):
    print('Number of arguments:', len(sys.argv), 'arguments.')
    print('Argument List:', str(sys.argv[1: ]))
    print("ERROR: Supply website, username and password")
    sys.exit()

site = sys.argv[1]
username = sys.argv[2]
pw = sys.argv[3]

driver = webdriver.Firefox()
driver.set_page_load_timeout(60*5)
driver.get("https://"+site+".club.hotmart.com/login")

def login():
    login = driver.find_element_by_name("login")
    login.clear()
    login.send_keys(username)

    password = driver.find_element_by_name("password")
    password.clear()
    password.send_keys(pw)

    password.send_keys(Keys.RETURN)

def get_page_list():
    list_of_articles = {}
    list_btn = driver.find_elements_by_class_name("content-navigation-page-name")[1]
    list_btn.click()

    time.sleep(2)

    list_article_p = driver.find_element_by_tag_name("article").find_element_by_tag_name("p").find_elements_by_tag_name("p")

    for article_p in list_article_p:
        try:
            link = article_p.find_element_by_tag_name('a')
            list_of_articles[link.text] = link.get_attribute("href")
        except:
            continue

    return list_of_articles

def extract_video_links(page_url):
    yt_videos = []


    print("Link: ", page_url)
    driver.get(page_url)
    time.sleep(4)
    driver.implicitly_wait(10)
    iframes = driver.find_elements_by_tag_name("iframe")

    for iframe in iframes:
        src = iframe.get_attribute("src")
        if "www.youtube.com" in src:
            yt_videos.append(src)
    return yt_videos

def delete_folder(name):
    if os.path.exists("./"+name):
        shutil.rmtree('./'+name)

def create_folder(name):
    if not os.path.exists("./"+name):
        os.makedirs("./"+name)
    return "./"+name

class VideoDownloader(object):
    @staticmethod
    def download_youtube_video(url, folder):
        yt = YouTube(url)
        yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download('./'+folder+'/')


class DownloadManager(object):
    def __init__(self, total_pages=None):
        self.TOTAL_THREADS = total_pages
        self.THREADS_DONE = 0

    def new_thread(self, video_links, folder):
        return DownloadThread(parent=self, video_links=video_links, folder=folder)

    def on_thread_finished(self):
        self.THREADS_DONE = self.THREADS_DONE + 1
        print("Done: " + str(self.THREADS_DONE+1) + "/" + str(self.TOTAL_THREADS))

class DownloadThread(Thread):

    def __init__(self, parent=None, video_links=None, folder=None):
        self.parent = parent
        self.video_links = video_links
        self.folder = folder
        super(DownloadThread, self).__init__()

    def run(self):
        print("In progess: " + str(self.parent.THREADS_DONE+1) + "/" + str(self.parent.TOTAL_THREADS))
        for video_link in self.video_links:
            VideoDownloader.download_youtube_video(video_link, self.folder)
        self.parent and self.parent.on_thread_finished()


def execution():
    FOLDER_NAME = "videos"

    delete_folder(FOLDER_NAME)
    create_folder(FOLDER_NAME)

    login()
    time.sleep(2)
    dict_of_pages = get_page_list()

    print(dict_of_pages)

    total_pages = len(dict_of_pages)

    download_manager = DownloadManager(total_pages=total_pages)

    for page_title in dict_of_pages:
        video_links = extract_video_links(dict_of_pages[page_title]);
        folder = create_folder(FOLDER_NAME+"/"+page_title);
        download_manager.new_thread(video_links, folder).start()

#try:
execution()
#except Exception as e:
#    print(e)
#    driver.close()
#    sys.exit()
