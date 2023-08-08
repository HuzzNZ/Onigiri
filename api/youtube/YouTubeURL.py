import os
import re
from typing import TypeVar, Type

import googleapiclient.discovery
from dotenv import load_dotenv

load_dotenv()
Y = TypeVar("Y")


class YouTubeURL:
    __api = googleapiclient.discovery.build("youtube", "v3", developerKey=os.getenv("YT_API"))
    __build_key = "abcd1234"
    url_regex = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+" \
                r"\?v=|embed\/|live\/|v\/)?)([\w\-]+)(\S+)?$"

    def __init__(self, _id: str, **kwargs) -> None:
        if kwargs.get("build_key", "") == YouTubeURL.__build_key:
            self._id = _id
        else:
            raise AttributeError("You must construct the YouTubeURL object through unsafe() or safe().")

    def get_short_url(self, start: str = "", end: str = "") -> str:
        return f"https://youtu.be/{self._id}" \
               f"{'?start=' + start if start else ''}{'&end=' + end if end else ''}"

    def get_url(self, start: str = "", end: str = "") -> str:
        return f"https://www.youtube.com/watch?v={self._id}" \
               f"{'&start=' + start if start else ''}{'&end=' + end if end else ''}"

    def get_id(self):
        return self._id

    @classmethod
    def unsafe(cls: Type[Y], url: str) -> Y:
        if not (match := re.search(YouTubeURL.url_regex, url, re.IGNORECASE)):
            raise ValueError("Specified URL is not a valid YouTube URL.")
        _id = match.group(6)
        if not (videos := YouTubeURL.__api.videos().list(part="snippet", id=_id).execute().get("items", [])):
            raise ValueError("Specified video cannot be found.")
        _id = videos[0]["id"]
        return cls(_id, build_key=cls.__build_key)

    @classmethod
    def safe(cls: Type[Y], url: str) -> Y:
        if not (match := re.search(YouTubeURL.url_regex, url, re.IGNORECASE)):
            raise ValueError("Specified URL is not a valid YouTube URL.")
        _id = match.group(6)
        return cls(_id, build_key=cls.__build_key)
