import logging


class Tester:
    def __init__(self, shiro):
        self.shiro = shiro
        self.message = None
        self.prefix = None

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

    def test_command(self, message_content):
        """Create fake ctx with command"""
        self.prefix = await self.shiro.get_prefix(self.message)
        self.message.content = "{0}{1}".format(self.prefix, message_content)
        self.shiro.invoke(self.shiro.get_context(self.message))

    async def test_general(self):
        """Run tests for every general command"""
        self.test_command("info")
        self.test_command("stats")
        self.test_command("oprequest \"TitleTest \"ReferenceTest \"https://www.youtube.com/watch?v=5_iuNaULT5k")
        self.test_command("edrequest \"TitleTest \"ReferenceTest \"https://www.youtube.com/watch?v=xhtC1YU2RME")
        self.test_command("ostrequest \"TitleTest \"ReferenceTest \"https://www.youtube.com/watch?v=TKeI8eYtWyQ&t=109s")

    async def test_songs(self):
        """Run test for every songs command"""
        self.test_command("opquiz \"1")
        self.test_command("edquiz \"1")
        self.test_command("ostquiz \"1")
        self.test_command("stop")

    async def test_settings(self):
        """Run test for every settings command"""
        self.test_command("prefix !")
        self.test_command("deletion on")
        self.test_command("channel {0}".format(self.shiro.config["tests"]["text_channel"]))
        self.test_command("language de")
        self.test_command("config")

    async def test_utility(self):
        """Run test for every utility command"""
        self.test_command("search Code")
        self.test_command("edittitle 19 COLORS")
        self.test_command("editreference 19 Code Geass")
        self.test_command("editurl 19 https://www.youtube.com/watch?v=cZ7zQbMxm28")
        self.test_command("editcategory 19 Opening")

