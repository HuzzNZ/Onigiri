# Onigiri Bot Documentation

Documentation page for the Onigiri Bot on discord.

Developed by **@Huzz#0009**. ****You can find me on twitter [@HuzzuDesu](https://twitter.com/HuzzuDesu)! 

# First-time setup


### [Invite the bot!](https://discord.com/api/oauth2/authorize?client_id=993098446187794462&permissions=8590198784&scope=bot%20applications.commands)

For first-time setup, run [/setup](https://www.notion.so/setup-a0ad166ca530437d8f1c19a79420a77f) to initialize the bot in the server. You’ll need to pick the channel the bot sends the schedule message in, as well setting an optional name for the talent the schedule is for.

# Functionality


The bot will send, and edit a message in a specified channel to be used as a schedule. The events are all user-inputted, and the bot only provides a framework to allow multiple users to contribute to a community-ran schedule of their favorite VTubers. By associating an event with an URL to a YouTube stream/premiere, the bot can automatically fill the details to that event from the URL!

- **Schedule message preview:**
    
    ![Untitled](https://s3.us-west-2.amazonaws.com/secure.notion-static.com/fce77fff-0766-4bbb-bac6-bbf98f92046d/Untitled.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=AKIAT73L2G45EIPT3X45%2F20220704%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20220704T060237Z&X-Amz-Expires=86400&X-Amz-Signature=ec67c7cdee5e78182ca56f5766582a0e4e9708dfb19733e5badfa187cfce2f84&X-Amz-SignedHeaders=host&response-content-disposition=filename%20%3D%22Untitled.png%22&x-id=GetObject)
    

Future updates also plan to enable the bot to create **Discord Events** based on events inputted into the bot.

# Commands


All commands have an **ephemeral** response. This means that only you can see the bot’s responses to your commands, so feel free to execute the commands in any channel.


💡 Commands with the `Manage Messages` permission can be executed by users who can manage messages in the **channel the schedule is hosted in**.


## Maintenance / Utility commands

All commands under the category of Maintenance and Utility.

## Event Creation commands

All commands under the category of Event Creation. **All events will be associated with a 4-digit numerical ID** (e.g. `1157`) to be referenced using Event Modification commands.

## Event Modification commands

All commands under the category of Event Modification. Every command requires the **ID** of an event as a parameter. This is the **4-digit numerical ID** (e.g. `1157`) assigned to events when they were created.

# Date/Time input formats


## Dates

Inputting dates is easy. The date parser accepts a wide range of date formats, and is not case sensitive: (Dates formatted like **22/07/12** should follow **y/m/d**.)

- July 12
- Jul 12 2022
- 12 Jul
- 7/12
- October 13, 2022

- 07/12
- 22/07/12
- 2022/7/12
- today
- tomorrow


💡 If there is no year specified, any date with the month **before** the current month will automatically be assumed to be in the **next year**. For example, if today is **December 12, 2022**, then inputting **Jan 4** will lead to it being recorded as **Jan 4, 2023**. You can override this by specifying the year.


💡 You can type **today** or **tomorrow** as a shorthand for the respective days. The bot will determine this based on JST, so **check if the time has passed midnight JST before using this shorthand**.


## Times

Inputting time is also easy, and not case sensitive. See the reference below: (**hh:mm** should be followed. **Do not specify seconds!**)

- 20:00
- 20
- 2000
- 25:15
- 24

- 8pm
- 8:00 pm
- 8PM
- 1:15am
- now


💡 You can type **now** as a shorthand for the current minute. Events with time set to the current minute will appear as a **Past Event**.


💡 Hours **beyond 23** are supported, as it is quite commonly used in Japan. Anything representing **24:00** until **29:59** will be recognized, and recorded as **0:00** until **5:59** the next day.

# YouTube Link Data Extraction


This bot uses Google’s **[YouTube Data API v3](https://developers.google.com/youtube/v3)** to extract information for use. Because of the limitations of this API, it is currently impossible to distinguish a **finished livestream** from a **premiered video**. As such, all finished livestreams or premiered videos that are longer than **15 minutes** will be considered a `stream` type, and anything under will be considered a `video`. You can use **/type** to edit this if it is inaccurate.
