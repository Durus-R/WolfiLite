import threading
import discord
import os
import time
import wikipedia
from g_crawl import GoogleImageCrawler
import praw
import contextlib
import re
import io
from flask import Flask
import wolframalpha
import lyricsgenius
token = os.environ['token']
wikipedia.set_lang("de")
print("[*] Language set for Wikipedia")
tempdir = "/tmp/py_crawl" # change this if you are using Windows!
g_crawler = GoogleImageCrawler(storage={'root_dir': tempdir})
print("[*] Google Image Crawler ready.")
app_id = os.environ['WolframAlpha']
client = wolframalpha.Client(app_id)

def wolfram(text):
    res = client.query(text)
    # Includes only text from the response
    return next(res.results).text


def strFactory(iterables, end=" "):
    try:
        s = ""
        for i in iterables:
            s += str(i)
            s += end
        return s
    except TypeError:
        return str(iterables)


def awakeWolfram():
    start = time.perf_counter()
    wolfram("3^18")
    t = time.perf_counter() - start
    print(f"[*] Buffertime to WolframAlpha: {t}")


t = threading.Thread(target=awakeWolfram)
t.start()
reddit = praw.Reddit(client_id=os.environ["Reddit_ID"],
                     client_secret=os.environ["Reddit_Secret"],
                     user_agent="Wolfi - made by u/TheDarkLink156")
memes = reddit.subreddit("memes").new(limit=20)
print(f"[*] Reddit logged in. Read-Only: {reddit.read_only}")
genius = lyricsgenius.Genius(os.environ["Genius"])

def imagedownload(topic):
  g_crawler.crawl(keyword=topic,  max_num=2)
  x = os.listdir("/tmp/py_crawler")
  return discord.File(os.path.join("/tmp/py_crawler", x[-1]))

  
class Client(discord.Client):
    async def on_ready(self):
        print("[*] Logged in as: ", self.user)
        await self.change_presence(activity=discord.Game(name="Mathematica"))

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content.startswith("?c "):
            
            s = message.content[3:]
            print(f"[*] Starting Query {s}")
            res_ = strFactory(wolfram(s))
            res = res_
            print(f"[*] Result: {res}")
            if res:
                await message.channel.send(
                    f"{message.author.mention}, i calculated: {res}")
            else:
                await message.channel.send(
                    f"{message.author.mention}, Sorry, but there is no answer. :confused:"
                )
            return
        if message.content.startswith("?w "):
            s = message.content[3:]
            print(f"[*] Starting Short Wikipedia query for {s}")
            try:
                res = wikipedia.summary(s, sentences=1)
                await message.channel.send(f"{message.author.mention} {res}")
            except wikipedia.exceptions.PageError:
                await message.channel.send(
                    f"{message.author.mention}, i couldn't get one articel. Did you write all correctly?"
                )
            except wikipedia.exceptions.DisambiguationError:
                await message.channel.send(
                    f"{message.author.mention}, your query matched more than once. Type ?ws <tilte> for show them all."
                )
            return
        if message.content.startswith("?wl "):
            s = message.content[4:]
            print(f"[*] starting default query for {s}")
            try:
                res = wikipedia.summary(s)
                await message.channel.send(f"{message.author.mention}, i found out:")
                if len(res) > 1800:
                  res1 = res[0:1800]
                  res2 = res[1800:]
                  await message.channel.send(res1)      
                  
                  await message.channel.send(res2)
                else:
                  await message.channel.send(
                    res
                  )
            except wikipedia.exceptions.PageError:
                await message.channel.send(
                    f"{message.author.mention},  couldn't get one articel. Did you write all correctly?"
                )
            except wikipedia.exceptions.DisambiguationError:
                await message.channel.send(
                    f"{message.author.mention}, your query matched more than once. Type ?ws <tilte> for show them all."
                )
            return

        if message.content.startswith("?ws "):
            s = message.content[3:]
            print(f"[*] Wikipedia-search on {s}")
            res_ = wikipedia.search(s)
            res = strFactory(res_, end="; ")
            if res_:
                await message.channel.send(
                    f"{message.author.mention}, your query resulted: {res}"
                )
            else:
                await message.channel.send(
                    f"{message.author.mention}, your query didn't match at least once. :confused:"
                )
        if message.content.startswith("?img "):
            s = message.content[5:]
            i = imagedownload(s)
            await message.channel.send(file=i)
            with contextlib.suppress(os.error):
              os.remove(os.path.join(tempdir, "000001.jpg"))
              os.remove(os.path.join(tempdir, "000002.jpg"))
            return
        if message.content.startswith("?m "):
            s = int(message.content[3:])
            global memes
            for i in range(s):
                try:
                    await message.channel.send(next(memes).url)
                except StopIteration:
                    memes = reddit.subreddit("memes").new(limit=20)
                    print("[*] refreshed memes")
                    await message.channel.send(next(memes).url)
            return

        if message.content == "?help":
            await message.channel.send("""[C] René Regensbogen 2020-21
            This Bot is licensed with the GPL, but it may contain indepent parts under different licenses.
            
?c -- lookup on Wolfram|Alpha for your question

?w -- very short summary (1 sentence) on this topic featuring Wikipedia.

?wl -- default-long summary on this topic featuring Wikipedia.

?ws <title> -- find all Wikipedia-articles including this title.

?img -- posts an image of Google with this topic.

?m -- posts i memes from reddit.com/r/memes

?l <title> by -- lookup the lyrics of the title by the singer

""")
            return

        r = re.match(r"\?l (.*) by (.*)", message.content)
        if r:
            song = r.group(1)
            artist = r.group(2)
            await message.channel.send("Wait a second, i'll search that...")
            sng = genius.search_song(song, artist)
            sng_ = io.StringIO(str(sng.lyrics))
            res = ""
            try:
                while True:
                    for i in range(5):
                        res += next(sng_)
                    await message.channel.send(res)
                    res = ""
            except StopIteration:
                print("[*] Lyrics sending Done.")
                return



if __name__ == "__main__":
    bot = Client()
    bot.run(token)
