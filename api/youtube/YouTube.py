import datetime
import os
from typing import Literal

import googleapiclient.discovery
import isodate
import pytz
from dotenv import load_dotenv

from api.youtube import YouTubeURL
from tools.constants import JST

load_dotenv()


class YouTube:
    def __init__(self, url: YouTubeURL):
        self.__api = googleapiclient.discovery.build("youtube", "v3", developerKey=os.getenv("YT_API"))
        self.__parts = "snippet, liveStreamingDetails, status, contentDetails"
        self.url: YouTubeURL = url
        self.video = self.__api.videos().list(part=self.__parts, id=self.url.get_id()).execute().get("items", [])[0]

    @property
    def start_time(self) -> datetime.datetime:
        def iso_to_datetime_jst(iso_time):
            return datetime.datetime.strptime(iso_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC).astimezone(JST)

        if ls_detail := self.video.get("liveStreamingDetails"):
            iso = ls_detail["scheduledStartTime"]
        else:
            iso = self.video["snippet"]["publishedAt"]
        return iso_to_datetime_jst(iso)

    @property
    def title(self) -> str:
        return self.video["snippet"]["title"]

    @property
    def channel(self) -> str:
        return self.video["snippet"]["channelTitle"]

    @property
    def content_type(self) -> Literal["stream", "video"]:
        scheduled_start_time = self.video.get('liveStreamingDetails', {}).get('scheduledStartTime')
        upload_status = self.video.get('status', {}).get('uploadStatus')
        live_broadcast_content = self.video.get("snippet", {}).get("liveBroadcastContent")
        duration = self.video.get("contentDetails", {}).get("duration", "")

        if not scheduled_start_time:
            return "video"  # it is a video
        future = live_broadcast_content == "upcoming" or live_broadcast_content == "live"
        if upload_status == "processed" and future:
            return "video"  # it is a premiere, treated as a video
        length = isodate.parse_duration(duration).seconds
        if length and length <= 900:
            return "video"  # treat livestreams with less than 15 minutes as premiere
        return "stream"


if __name__ == "__main__":
    vid2 = YouTube(YouTubeURL.unsafe("https://www.youtube.com/watch?v=5a8NyGLlorI"))
    vid3 = YouTube(YouTubeURL.unsafe("https://www.youtube.com/watch?v=Akn_Gdi05Ys"))
    print(vid2.title, vid2.channel, vid2.start_time, vid2.content_type, vid2.url.get_short_url())
    print(vid3.title, vid3.channel, vid3.start_time, vid3.content_type, vid3.url.get_short_url())
