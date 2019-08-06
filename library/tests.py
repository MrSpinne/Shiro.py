class Tester:
    def __init__(self, shiro):
        self.shiro = shiro
        self.message = None

    async def run(self):
        """Start tests"""
        await self.create_message()
        await self.test_general()
        await self.test_songs()
        await self.test_settings()
        await self.test_utility()

    async def create_message(self):
        """Create fake message"""
        text_channel = await self.shiro.fetch_channel(self.shiro.config["tests"]["text_channel"])
        voice_channel = await self.shiro.fetch_channel(self.shiro.config["tests"]["voice_channel"])
        self.message = await text_channel.send("Starting tests!")
        self.message.author.voice.channel = voice_channel

    async def test_command(self, message_content):
        """Create fake ctx with command"""
        prefix = await self.shiro.get_prefix(self.message)
        self.message.content = "{0}{1}".format(prefix, message_content)
        self.shiro.invoke(await self.shiro.get_context(self.message))

    async def test_general(self):
        """Run tests for every general command"""
        await self.test_command("info")
        await self.test_command("stats")
        await self.test_command("oprequest Test Test https://www.youtube.com/watch?v=5_iuNaULT5k")
        await self.test_command("edrequest \"Test Test\" Test https://www.youtube.com/watch?v=xhtC1YU2RME")
        await self.test_command("ostrequest ´\"Test Test\" \"Test Test\" https://www.youtube.com/watch?v=TKeI8eYtWyQ&t=109s")

    async def test_songs(self):
        """Run test for every songs command"""
        await self.test_command("opquiz 1")
        await self.test_command("edquiz 1")
        await self.test_command("ostquiz 1")
        await self.test_command("stop")

    async def test_settings(self):
        """Run test for every settings command"""
        await self.test_command("prefix !")
        await self.test_command("deletion on")
        await self.test_command("channel {0}".format(self.shiro.config["tests"]["text_channel"]))
        await self.test_command("language de")
        await self.test_command("config")

    async def test_utility(self):
        """Run test for every utility command"""
        await self.test_command("search Code")
        await self.test_command("edittitle 19 COLORS")
        await self.test_command("editreference 19 Code Geass")
        await self.test_command("editurl 19 https://www.youtube.com/watch?v=cZ7zQbMxm28")
        await self.test_command("editcategory 19 Opening")
