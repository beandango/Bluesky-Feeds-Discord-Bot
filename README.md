# Bluesky Feed Discord Bot

This bot was made for content creators or streamers in mind who might want to have a custom bot in their discord server that relays all of their Bluesky posts to a specified channel

Currently, it supports posts, reposts, replies, and quote reposts (kind of, as in, it only shows the content of your post and not the one you're quoting). I may add a feature to change these settings during setup later on.

This documentation will hopefully go through everything you need to know/do to make this work, even if you have absolutely no clue how any discord bot stuff works.

# Commands 
## (Note! Until Issue #1 is fixed, commands are broken! OOPS! Check back for the next pre-release where these commands are actually relevant!)
### /setup
Use this command to begin the setup process for your bluesky feed. You need to be admin to use this command. You'll also need to grab the `channel id` of whatever channel you want the updates posted in. Do that by right clicking on the channel, and clicking `copy channel id`. 

<b>*Note: /setup currently is BROKEN. You NEED to edit the config. Visit the [Config](#config) section of this readme for more details on that.)</b>

### /help
A help command. It basically tells you the same stuff as here. 

### /getpost
This is a command originally created for debugging purposes. It allows you to immediately grab the latest post from bluesky. (*Note, it may not work immediately after starting up the bot. This is... I guess not necessarily intended, but normal.)
The `hidden` option refers to this: ![image](https://github.com/user-attachments/assets/13768c5f-eefd-40cc-b357-871e78a21743)

If `hidden` is set to True, it sends the post as an ephemeral message, meaning only you can see it. Otherwise, it'll be a normal post like any other.

# Tutorial

### Things you need
- A computer you can run an exe on 24/7 or some sort of hosting service you've subscribed to that can do it for you. 
- discord developer mode turned on. You'll need it to grab a channel id when setting up the bot in your server. [Here's how to do that.](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID)

## Create Discord App
- Log into discord on web and navigate to the [Discord Developer Portal](https://discord.com/developers/applications)
- Create an application and name it what you'd like. This is where you can customize the profile image and About Me section of the bot.
- Under the Installation tab, copy the following: ![image](https://github.com/user-attachments/assets/3c2ba86e-fc31-4295-9ca7-dbb910352a70)
- Now go to the `Bot` tab. Here you can add a banner image if you'd like and customize the bot's username.
- More importantly, scroll down to `Authorization Flow`. Copy the following: ![image](https://github.com/user-attachments/assets/b1b9a866-2892-4b85-a780-16529df97b1d)
- Save, and scroll back up and hit `Reset Token`. Put this in notepad or something, you'll need it soon.
- Now head to the `Oauth2` tab. You'll need to select the scopes `bot` and `applications.commands` ![image](https://github.com/user-attachments/assets/6b46f8e0-a69b-4024-abeb-fd17125c2e94)
- And the bot permissions it needs are at minimum `Send messages` and `Use Slash Commands`, but you are welcome to just give it `Administrator`.
- Note! If you do not give the bot Admin permissions, then when in your server, `make sure it both has access to the channel you want it to post in, AND it has permissions to send messages into that channel.` It's easy to forget that second part.
- Scroll down and there should now be a generated url. Use that to invite your new bot to your server!

## Config!
- Unzip the .zip folder linked in the `Releases` section of this repo
- Run bsky.exe, it will create a config.json file for you in the same directory as the exe.
- Open up the Json with a text editor (you can change the file extension from .json to .txt, just change it back to .json when you're done editing)
- You'll need to put your bot token in the `TOKEN` field, keeping the ""s. (Example: TOKEN = "blahblahblahtokenhere")
- Put your channel id in the `CHANNEL_ID` field. `Make sure there are NO "quotes"!` (Example: CHANNEL_ID = 1234567890)
- Put the desired bluesky handle in the `BLSKY_USER_HANDLE` field. (Example: BLSKY_USER_HANDLE = "beandango.bizren.moe")

# Support
If you run into any issues and my documentation is confusing or unhelpful, please let me know! You can reach me on discord as `beandango` or on bluesky as `beandango.bizren.moe` :)

You are also welcome to create any Issues for any suggestions, bug fixes, questions, etc.

I am still quite amateur at writing code, so I know my code may be completely spaghetti. Ultimately I want this bot to be convenient and helpful to others, so feel free to contribute! Even just creating issues is great contribution.


