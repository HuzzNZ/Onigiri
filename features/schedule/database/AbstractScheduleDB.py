import datetime
from abc import abstractmethod
from typing import Optional, List, Literal

from features.schedule.models import Event, DatetimeGranularity, GuildScheduleConfig


class AbstractScheduleDB:
    @abstractmethod
    async def get_guild_exists(self, guild_id: int) -> bool:
        """
        Checks if a guild exists.

        :param guild_id: The ID of the guild.
        :return: bool
        """

    @abstractmethod
    async def get_event_exists(self, guild_id, event_id: str) -> bool:
        """
        Checks if an event exists.

        :param guild_id: The ID of the guild that is associated with the event.
        :param event_id: The ID of the event.
        :return: bool
        """

    @abstractmethod
    async def get_available_event_id(self, guild_id) -> str:
        """
        Gets an available event ID to use for a guild.
        
        :param guild_id: The ID of the guild to get an available event ID for.
        :return: str
        """

    @abstractmethod
    async def get_guild(self, guild_id: int) -> Optional[GuildScheduleConfig]:
        """
        Gets a guild's config.

        :param guild_id: The ID of the guild.
        :return: Optional[GuildScheduleConfig]
        """

    @abstractmethod
    async def get_all_guilds(self) -> List[GuildScheduleConfig]:
        """
        Gets all guilds' configs.

        :return: List[GuildScheduleConfig]
        """

    @abstractmethod
    async def get_enabled_guilds(self) -> List[GuildScheduleConfig]:
        """
        Gets all guilds' configs with schedule enabled.

        :return: List[GuildScheduleConfig]
        """

    @abstractmethod
    async def get_event(self, guild_id: int, event_id: str) -> Optional[Event]:
        """
        Gets an event.

        :param guild_id: The ID of the guild that the event is associated to.
        :param event_id: The ID of the event.
        :return: Optional[Event]
        """

    @abstractmethod
    async def get_all_events(self, guild_id: int) -> List[Event]:
        """
        Gets all events for a guild.

        :param guild_id: The ID of the guild.
        :return: List[Event]
        """

    @abstractmethod
    async def get_guild_events(self, guild_id: int) -> List[Event]:
        """
        Gets all events for a guild.

        :param guild_id: The ID of the guild.
        :return: List[Event]
        """

    @abstractmethod
    async def create_guild(self, guild: GuildScheduleConfig) -> GuildScheduleConfig:
        """
        Creates a guild's configs.

        :param guild: GuildScheduleConfig
        :return: GuildScheduleConfig
        """

    @abstractmethod
    async def create_event(self, event: Event) -> Event:
        """
        Creates an event for a guild.

        :param event: Event
        :return: Event
        """

    @abstractmethod
    async def update_guild(self, guild_id: int, guild: GuildScheduleConfig) -> GuildScheduleConfig:
        """
        Updates a guild's configs.

        :param guild_id: The ID of the guild's configs to update.
        :param guild: GuildScheduleConfig
        :return: GuildScheduleConfig
        """

    @abstractmethod
    async def update_event(self, guild_id: int, event_id: str, event: Event) -> Event:
        """
        Updates an event.

        :param guild_id: The ID of the guild that the event is associated with.
        :param event_id: The ID of the event to update.
        :param event: Event
        :return: Event
        """

    @abstractmethod
    async def delete_guild(self, guild_id: int) -> None:
        """
        Deletes a guild's configs.

        :param guild_id: The ID of the guild's configs to delete.
        :return: None
        """

    @abstractmethod
    async def delete_event(self, guild_id: int, event_id: str) -> None:
        """
        Deletes an event.

        :param guild_id: The ID of the guild that the event is associated with.
        :param event_id: The ID of the event to delete.
        :return:
        """

    @abstractmethod
    async def set_guild_enable(self, guild_id: int) -> None:
        """
        Sets a guild to be enabled.

        :param guild_id: The ID of the guild.
        :return: None
        """

    @abstractmethod
    async def set_guild_disable(self, guild_id: int) -> None:
        """
        Sets a guild to be disabled.

        :param guild_id: The ID of the guild.
        :return: None
        """

    @abstractmethod
    async def set_guild_talent(self, guild_id: int, talent: str) -> None:
        """
        Sets the talent of a guild.

        :param guild_id: The ID of the guild.
        :param talent: The talent of the guild.
        :return: None
        """

    @abstractmethod
    async def set_guild_description(self, guild_id: int, talent: str) -> None:
        """
        Sets the description of a guild.

        :param guild_id: The ID of the guild.
        :param talent: The talent of the guild.
        :return: None
        """

    @abstractmethod
    async def set_guild_channel(self, guild_id: int, schedule_channel: int) -> None:
        """
        Sets the channel of the schedule messages in the guild.

        :param guild_id: The ID of the guild.
        :param schedule_channel: The ID of the schedule channel.
        :return: None
        """

    @abstractmethod
    async def set_guild_messages(self, guild_id: int, schedule_messages: List[int]) -> None:
        """
        Sets the channel of the schedule messages in the guild.

        :param guild_id: The ID of the guild.
        :param schedule_messages: A list of IDs of the schedule messages.
        :return: None
        """

    @abstractmethod
    async def set_guild_editors(self, guild_id: int, editors: List[int]) -> None:
        """
        Sets the channel of the schedule messages in the guild.

        :param guild_id: The ID of the guild.
        :param editors: A list of IDs of the schedule editor roles.
        :return: None
        """

    @abstractmethod
    async def set_event_title(self, guild_id: int, event_id: str, title: str) -> None:
        """
        Sets the title of an event.

        :param guild_id: The ID of the guild that the event is associated to.
        :param event_id: The ID of the event.
        :param title: The title of the event.
        :return: None
        """

    @abstractmethod
    async def set_event_datetime(self, guild_id: int, event_id: str, dt: datetime.datetime) -> None:
        """
        Sets the datetime of an event.

        :param guild_id: The ID of the guild that the event is associated to.
        :param event_id: The ID of the event.
        :param dt: The start time of the event.
        :return: None
        """

    @abstractmethod
    async def set_event_datetime_granularity(self, guild_id: int, event_id: str, dt_g: DatetimeGranularity) -> None:
        """
        Sets the datetime granularity of an event.

        :param guild_id: The ID of the guild that the event is associated to.
        :param event_id: The ID of the event.
        :param dt_g: The datetime granularity of the event.
        :return: None
        """

    @abstractmethod
    async def set_event_type(self, guild_id: int, event_id: str, t: Literal[0, 1, 2, 3, 4]) -> None:
        """
        Sets the type on an event.

        :param guild_id: The ID of the guild that the event is associated to.
        :param event_id: The ID of the event.
        :param t: The type of the event.
        :return: None
        """

    @abstractmethod
    async def set_event_confirmed(self, guild_id: int, event_id: str, confirmed: bool) -> None:
        """
        Sets an event's confirmed status.

        :param guild_id: The ID of the guild that the event is associated to.
        :param event_id: The ID of the event.
        :param confirmed: Event's confirmed status.
        :return: None
        """

    @abstractmethod
    async def set_event_stashed(self, guild_id: int, event_id: str, stashed: bool) -> None:
        """
        Sets an event's stashed status.

        :param guild_id: The ID of the guild that the event is associated to.
        :param event_id: The ID of the event.
        :param stashed: Event's stashed status.
        :return: None
        """

    @abstractmethod
    async def set_event_url(self, guild_id: int, event_id: str, url: str) -> None:
        """
        Sets the URL of an event.

        :param guild_id: The ID of the guild that the event is associated to.
        :param event_id: The ID of the event.
        :param url: The URL of the event.
        :return: None
        """

    @abstractmethod
    async def set_event_note(self, guild_id: int, event_id: str, note: str) -> None:
        """
        Sets the note of an event.

        :param guild_id: The ID of the guild that the event is associated to.
        :param event_id: The ID of the event.
        :param note: The note of the event.
        :return: None
        """
