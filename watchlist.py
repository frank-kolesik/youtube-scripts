from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import sqlite3
import pickle
import os


from utils import (
    get_function_name,
    get_watchlist_path,
)


class Watchlist():
    SCOPES = [
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"

    def __init__(self, watchlist_id):
        self.watchlist_id = watchlist_id

        paths = get_watchlist_path()
        self.database_path = paths.get("database")
        self.client_secret_path = paths.get("client_secret")
        self.client_token_path = paths.get("client_token")

        self.prepare_database()
        self.prepare_api()

    def prepare_database(self):
        con = sqlite3.connect(self.database_path)
        cursor = con.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS channels (
            channelId VARCHAR(50) NOT NULL,
            channelName VARCHAR(50) NOT NULL,
            playlistId VARCHAR(50) NOT NULL,
            PRIMARY KEY (channelId)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS history (
            id INTEGER,
            videoId VARCHAR(50) NOT NULL,
            videoPublished VARCHAR(50) NOT NULL,
            PRIMARY KEY (id)
        )''')

        con.close()

    def prepare_api(self):
        credentials = None

        if os.path.exists(self.client_token_path):
            print(f"[{get_function_name()}] Loading credentials")
            with open(self.client_token_path, "rb") as f:
                credentials = pickle.load(f)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                print(f"[{get_function_name()}] Refreshing credentials")
                credentials.refresh(Request())
            else:
                print(f"[{get_function_name()}] Getting credentials")
                os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
                credentials = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_path, self.SCOPES
                ).run_console()
            print(f"[{get_function_name()}] Saving credentials")
            with open(self.client_token_path, "wb") as f:
                pickle.dump(credentials, f)

        self.youtube = build(
            self.API_SERVICE_NAME,
            self.API_VERSION,
            credentials=credentials,
        )

    def get_channels_by_channel_name(self, channel_name):
        print(f"[{get_function_name()}]", channel_name)
        try:
            response = self.youtube.search().list(
                part="snippet",
                type="channel",
                q=channel_name,
            ).execute()

            channels = [{
                "id": item["snippet"]["channelId"],
                "name": item["snippet"]["channelTitle"],
                "description": item["snippet"]["description"],
                "image": item["snippet"]["thumbnails"]["default"],
            } for item in response["items"]]

            return channels
        except:
            return []

    def get_uploads_id_by_channel_id(self, channel_id):
        print(f"[{get_function_name()}]", channel_id)
        try:
            response = self.youtube.channels().list(
                part="contentDetails",
                id=channel_id,
            ).execute()

            uploads_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

            return uploads_id
        except:
            return None

    def get_uploads_by_uploads_id(self, uploads_id):
        print(f"[{get_function_name()}]", uploads_id)
        try:
            response = self.youtube.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_id,
            ).execute()

            recent_videos = [{
                "id": item["contentDetails"]["videoId"],
                "published": item["contentDetails"]["videoPublishedAt"],
            } for item in response["items"]]

            return recent_videos
        except:
            return []

    def add_to_playlist_by_video_id(self, video_id):
        print(f"[{get_function_name()}]", video_id)
        try:
            self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": self.watchlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id,
                        }
                    }
                }
            ).execute()
            return True
        except:
            return False

    def read_all_channels_from_database(self):
        con = sqlite3.connect(self.database_path)
        cursor = con.cursor()

        cursor.execute('''SELECT * FROM channels''')

        results = cursor.fetchall()
        con.close()

        return results

    def read_channels_from_database(self, channel_name):
        con = sqlite3.connect(self.database_path)
        cursor = con.cursor()

        cursor.execute('''SELECT * FROM channels
            WHERE channelName LIKE "%s"
        ''' % channel_name)

        results = cursor.fetchall()
        con.close()

        return results

    def write_channel_to_database(self, channel_id, channel_name, playlist_id):
        con = sqlite3.connect(self.database_path)
        cursor = con.cursor()

        cursor.execute('''INSERT INTO channels
            (channelId, channelName, playlistId)
            VALUES ("%s", "%s", "%s")
        ''' % (channel_id, channel_name, playlist_id))

        con.commit()
        con.close()

    def add_channel_to_database(self, channel_name):
        def get_bounded_index(upper):
            while True:
                try:
                    option = int(input("Choose an option to proceed! "))
                    if 0 <= option <= upper:
                        return option
                except:
                    pass

        print(f"[{get_function_name()}]", channel_name)
        channels = self.read_channels_from_database(channel_name)
        if channels:
            print(f"[{get_function_name()}] database", channel_name)
            for num, (channel_id, channel_name, _) in enumerate(channels):
                output = f"[{channel_name}] https://www.youtube.com/channel/{channel_id}"
                print(num, output)

            num += 1
            print(num, "[Channel Not Found]")

            option = get_bounded_index(num)
            if option < num:
                return print(f"[{get_function_name()}] Channel already in db")

        channels = self.get_channels_by_channel_name(channel_name)
        if not channels:
            return print(f"[{get_function_name()}] No Channels found")

        for num, channel in enumerate(channels):
            channel_id = channel["id"]
            channel_name = channel["name"]
            channel_description = channel["description"].strip()
            output = f"[{channel_name}] https://www.youtube.com/channel/{channel_id}"
            print(num, output)
            if channel_description:
                print("> Description", channel_description)

        num += 1
        print(num, "[Channel Not Found]")

        option = get_bounded_index(num)
        if option == num:
            return print(f"[{get_function_name()}] Channel Not Found")

        channel = channels[option]

        channel_id = channel["id"]
        channel_name = channel["name"]
        playlist_id = self.get_uploads_id_by_channel_id(channel_id)

        self.write_channel_to_database(channel_id, channel_name, playlist_id)

    def add_videos_to_watchlist(self):
        print(f"[{get_function_name()}] started")
        con = sqlite3.connect(self.database_path)
        cursor = con.cursor()
        channels = self.read_all_channels_from_database()

        for _, _, playlist_id in channels:
            uploads = self.get_uploads_by_uploads_id(playlist_id)
            for upload in uploads:
                video_id = upload["id"]
                video_published = upload["published"][:10]

                cursor.execute('''SELECT * FROM history
                    WHERE videoId = "%s"
                ''' % video_id)

                if cursor.fetchone() is not None:
                    print(f"[{get_function_name()}] video already added")
                    continue

                added = self.add_to_playlist_by_video_id(video_id)

                if not added:
                    print(f"[{get_function_name()}] error: video not added")
                    continue

                print(f"[{get_function_name()}] video added to watchlist & db")
                cursor.execute('''INSERT INTO history
                    (videoId, videoPublished)
                    VALUES ("%s", "%s")
                ''' % (video_id, video_published))

        con.commit()
        con.close()
        print(f"[{get_function_name()}] finished")
