import bookmarks_parser
import youtube_dl
import inspect
import os


def get_function_name(): return inspect.stack()[1][3]


def get_project_path():
    print("[setup_project]")
    document_path = os.path.expanduser('~/Documents')
    project_path = f"{document_path}/youtube-scripts"
    os.makedirs(project_path, exist_ok=True)
    return project_path


class Downloader():

    def __init__(self):
        self.project = get_project_path()

    def parse_bookmarks(self, bookmarks_file, bookmarks_folder):
        print(f"[{get_function_name()}] parsing", bookmarks_file)
        bookmarks = bookmarks_parser.parse(bookmarks_file)

        print(f"[{get_function_name()}] filtering folder:", bookmarks_folder)
        folder = list(filter(lambda x: x["type"] == "folder" and x["title"]
                      == bookmarks_folder, bookmarks[0]["children"])).pop()

        print(f"[{get_function_name()}] filtering bookmarks")
        bookmarks = [{
            "title": x["title"],
            "url": x["url"],
        } for x in folder["children"] if x["type"] == "bookmark"]

        return bookmarks

    def download_mp3_from_url(self, url, retry=True):
        try:
            info = youtube_dl.YoutubeDL().extract_info(url=url, download=False)
            filename = f"{self.project}/{info['title']}.mp3"
            options = {
                'format': 'bestaudio',  # bestaudio, worstaudio
                'keepvideo': False,
                'outtmpl': filename,
            }
            with youtube_dl.YoutubeDL(options) as ydl:
                ydl.download([info['webpage_url']])
        except Exception as e:
            print(f"[{get_function_name()}] error:", e)
            if retry:
                self.download_mp3_from_url(url, retry=False)

    def download_mp3_from_bookmarks(self, bookmarks_file, bookmarks_folder):
        print(f"[{get_function_name()}] started downloads")
        bookmarks = self.parse_bookmarks(bookmarks_file, bookmarks_folder)

        for bookmark in bookmarks:
            print(f"[{get_function_name()}] download:", bookmark["title"])
            self.download_mp3_from_url(bookmark["url"])

        print(f"[{get_function_name()}] finished downloads")


if __name__ == "__main__":

    bookmarks_file = 'bookmarks_28.03.22.html'
    bookmarks_folder = 'music'

    dl = Downloader()
    dl.download_mp3_from_bookmarks(bookmarks_file, bookmarks_folder)
