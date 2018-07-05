import os
import time
import shutil
import sys
from threading import Thread

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
#from pytube import YouTube
import youtube_dl

if (len(sys.argv) < 4):
    print('Number of arguments:', len(sys.argv), 'arguments.')
    print('Argument List:', str(sys.argv[1: ]))
    print("ERROR: Supply website, username and password")
    sys.exit()

site = sys.argv[1]
username = sys.argv[2]
pw = sys.argv[3]

domain = "https://"+site+".club.hotmart.com"

driver = webdriver.Firefox()
driver.set_page_load_timeout(60*5)
driver.get(domain+"/login")

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
    time.sleep(2)
    driver.implicitly_wait(10)
    modules = driver.find_element_by_id("navigation-modules").find_elements_by_class_name("card")

    for module in modules:
        time.sleep(2)
        driver.implicitly_wait(10)
        module.click()

        driver.implicitly_wait(10)
        pages = module.find_element_by_class_name("navigation-module-pages").find_elements_by_class_name("navigation-page")

        for page in pages:

            page.find_element_by_class_name("navigation-page-info").find_element_by_class_name("navigation-page-title")
            driver.implicitly_wait(10)
            page.click()

            list_of_articles[page.text] = driver.current_url

    return list_of_articles

def extract_video_links(page_url):
    videos = []

    print("Link: ", page_url)
    time.sleep(2)
    driver.implicitly_wait(20)
    driver.get(page_url)
    time.sleep(4)
    driver.implicitly_wait(30)
    iframes = driver.find_elements_by_tag_name("iframe")

    for iframe in iframes:
        src = iframe.get_attribute("src")
        if "youtube" in src:
            videos.append(("youtube", src))
        elif "vimeo" in src:
            videos.append(("vimeo", src))

    return videos

def delete_folder(name):
    if os.path.exists("./"+name):
        shutil.rmtree('./'+name)

def create_folder(name):
    if not os.path.exists("./"+name):
        os.makedirs("./"+name)
    return "./"+name

class VideoDownloader(object):
    #@staticmethod
    #def download_youtube_video(url, folder):
    #    YouTube(url).streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download('./'+folder+'/')

    @staticmethod
    def download_video(url, folder):
        print("URL: ", url)
        youtube_dl.utils.std_headers['Referer'] = domain
        ydl_opts = {
            'outtmpl': './'+folder+'/%(title)s.%(ext)s',
            'quiet': True
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

class DownloadManager(object):
    def __init__(self, total_pages=None):
        self.TOTAL_THREADS = total_pages
        self.THREADS_DONE = 0

    def new_thread(self, videos, folder):
        return DownloadThread(parent=self, videos=videos, folder=folder)

    def on_thread_finished(self):
        self.THREADS_DONE = self.THREADS_DONE + 1
        print("Done: " + str(self.THREADS_DONE+1) + "/" + str(self.TOTAL_THREADS))

class DownloadThread(Thread):

    def __init__(self, parent=None, videos=None, folder=None):
        self.parent = parent
        self.videos = videos
        self.folder = folder
        super(DownloadThread, self).__init__()

    def run(self):
        print("In progess: " + str(self.parent.THREADS_DONE+1) + "/" + str(self.parent.TOTAL_THREADS))
        for video in self.videos:
            done = None
            while done is None:
                try:
                    VideoDownloader.download_video(video[1], self.folder)
                    done = True
                except:
                    pass
        self.parent and self.parent.on_thread_finished()


def execution():
    FOLDER_NAME = "videos"

    delete_folder(FOLDER_NAME)
    create_folder(FOLDER_NAME)

    login()
    time.sleep(2)
    dict_of_pages = get_page_list()

    download_manager = DownloadManager(total_pages=len(dict_of_pages))

    for page_title in dict_of_pages:
        videos = extract_video_links(dict_of_pages[page_title]);
        folder = create_folder(FOLDER_NAME+"/"+page_title);
        download_manager.new_thread(videos, folder).start()

#try:
execution()
#except Exception as e:
#    print(e)
#    driver.close()
#    sys.exit()
