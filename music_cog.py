import discord
from discord.ext import commands
from youtube_dl import YoutubeDL


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # all the music related stuff

        self.is_playing = False

        # 2d array containing [song, channel]

        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}

        self.vc = ""

    # searching the item on youtube

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception:
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            # get the first url

            m_url = self.music_queue[0][0]['source']

            # remove the first element as you are currently playing it

            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    # infinite loop checking

    async def play_music(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']

            # try to connect to voice channel if you are not already connected

            if self.vc == "" or not self.vc.is_connected() or self.vc is None:
                self.vc = await self.music_queue[0][1].connect()
            else:
                await self.vc.move_to(self.music_queue[0][1])

            print(self.music_queue)

            # remove the first element as you are currently playing it

            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    @commands.command(name="p", help="Plays a selected song from youtube")
    async def p(self, ctx, *args):
        query = " ".join(args)
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:

            # you need to be connected so that the bot knows where to go

            await ctx.send("Connect to a voice channel!")
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send(
                    "Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.")
            else:
                await ctx.send("Song added to the queue")
                self.music_queue.append([song, voice_channel])

                await self.q(ctx)

                if not self.is_playing:
                    await self.play_music()

    @commands.command(name="q", help="Displays the current songs in queue")
    async def q(self, ctx):
        await ctx.send("Current playlist:")

        retval = ""
        for i in range(0, len(self.music_queue)):
            retval += self.music_queue[i][0]['title'] + "\n"

        print(retval)
        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in playlist")

    @commands.command(name="skip", help="Skips the current song being played")
    async def skip(self, ctx):
        if self.vc != "" and self.vc:
            self.vc.stop()

            # try to play next in the queue if it exists

            await ctx.send("Song skipped.")
            await self.q(ctx)

    @commands.command(name="disconnect", help="Disconnecting bot from VC")
    async def dc(self, ctx):
        await self.vc.disconnect()

    @commands.command(name='stop', help="Stops the music")
    async def stop(self, ctx):
        if self.vc != "" and self.vc:
            self.vc.stop()
        else:
            await ctx.send("The bot is not playing anything at the moment.")

    @commands.command(name='pause', help="pauses music")
    async def pause(self, ctx):
        self.vc = ctx.voice_client
        if not self.vc or not self.vc.is_playing():
            embed = discord.Embed(title="", description="I am currently not playing anything")

            return await ctx.send(embed=embed)

        elif self.vc.is_paused():

            return

        self.vc.pause()
        await ctx.send("Paused ️")

    @commands.command(name='resume', help="resumes music")
    async def resume(self, ctx):
        self.vc = ctx.voice_client
        if not self.vc or not self.vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel")

            return await ctx.send(embed=embed)

        elif not self.vc.is_paused():

            return

        self.vc.resume()
        await ctx.send("Resuming ️")

