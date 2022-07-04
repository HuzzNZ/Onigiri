import datetime

import pytz
from dotenv import load_dotenv
import os
import isodate

import googleapiclient.discovery

load_dotenv()


class YouTubeURL:
    def __init__(self, v_id: str):
        api_service_name = "youtube"
        api_version = "v3"

        self.__api = googleapiclient.discovery.build(api_service_name, api_version, developerKey=os.getenv("YT_API"))

        self.__part = "snippet, liveStreamingDetails, status, contentDetails"
        self.v_id = v_id
        self.__premiere_or_stream_cutoff = 900

        self.url = ""
        self.valid = False
        self.__video = {}
        self.check_valid()

        if self.valid:
            self.type = None  # 0 for stream, 1 for premiere, 2 for video
            self.check_type()

    def __repr__(self):
        if not self.valid:
            return f"<Invalid YouTubeURL Object id={self.v_id}>"
        else:
            return f"<YouTubeURL Object id={self.v_id}, " \
                   f"title={self.get_event_title()}, " \
                   f"type={self.get_event_type()}, time={self.get_datetime_jst()}, " \
                   f"link={self.url}>"

    def check_valid(self):
        videos = self.__api.videos().list(part=self.__part, id=self.v_id).execute().get("items", [])
        if videos:
            self.valid = True
            self.url = f"https://youtu.be/{self.v_id}"
            self.__video: dict = videos[0]
        else:
            self.valid = False

    def check_type(self):
        upload_status = self.__video.get('status', {}).get('uploadStatus')
        scheduled_start_time = self.__video.get('liveStreamingDetails', {}).get('scheduledStartTime')
        live_broadcast_content = self.__video.get("snippet", {}).get("liveBroadcastContent")
        duration = self.__video.get("contentDetails", {}).get("duration", "")

        if not scheduled_start_time:
            self.type = 2
        else:
            in_future = live_broadcast_content == "upcoming" or live_broadcast_content == "live"
            if upload_status == "processed" and in_future:
                self.type = 1
            else:
                if not in_future:
                    length = isodate.parse_duration(duration).seconds
                    if length <= self.__premiere_or_stream_cutoff:
                        self.type = 1
                    else:
                        self.type = 0
                else:
                    self.type = 0

    def get_datetime_jst(self):
        def iso_to_datetime_jst(iso: str) -> datetime.datetime:
            return datetime.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Tokyo"))
        match self.type:
            case 0 | 1:
                return iso_to_datetime_jst(self.__video.get('liveStreamingDetails', {}).get('scheduledStartTime'))
            case 2:
                return iso_to_datetime_jst(self.__video.get('snippet', {}).get('publishedAt'))

    def get_event_type(self):
        match self.type:
            case 0:
                return 0
            case 1 | 2:
                return 1

    def get_event_title(self):
        title = self.__video.get("snippet", {}).get("title", "An Event")
        if len(title) > 27:
            title = title[:24] + "..."
        return title


def main():
    print(YouTubeURL("pm6qb1UOiXo"))
    print(YouTubeURL("rKMhl43RHo0"))
    print(YouTubeURL("j1Bu3j32_1U"))
    print(YouTubeURL("7ollgEy5hjs"))
    print(YouTubeURL("h-bqYRzxROQ"))


if __name__ == "__main__":
    main()
