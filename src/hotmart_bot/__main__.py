import argparse
import os
from re import S


from hotmart_bot.bot.hotmart_bot import HotmartBot
from hotmart_bot.video_download.download_manager import DownloadManager



def create_parser() -> argparse.ArgumentParser:
    hotmart_parser = argparse.ArgumentParser(description="Download a course in Hotmart")

    hotmart_parser.add_argument("site", type=str, help="Name of course site.")
    hotmart_parser.add_argument(
        "-usr", "--username", help="Your username to login on Hotmart."
    )
    hotmart_parser.add_argument("-pwd", "--password", help="Your account password.")
    hotmart_parser.add_argument("-ef", "--envfile", help="Use env file.", action='store_true')
    hotmart_parser.add_argument(
        "-o", "--output_path", help="Path to store downloaded videos."
    )
    
    return hotmart_parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    SITE = args.site
    if args.envfile:
        USERNAME = os.getenv("ACCOUNT_USERNAME")
        PWD = os.getenv("PASSWORD")
    else:
        USERNAME = args.username
        PWD = args.password

    hb = HotmartBot()

    hb.login(SITE, USERNAME, PWD)
    modules = hb.get_modules_list()
    download_manager = DownloadManager(len(modules))

    for module in modules:
        if args.output_path:
            module.create_folder(args.output_path)
        else:
            module.create_folder()

        module.lessons = hb.get_lessons_list(module)
        
        # for lesson in module.lessons:
        #     lesson.create_folder(module)
        #     download_manager.new_thread(lesson.videos, lesson.path, SITE).start()


if __name__ == "__main__":
    main()