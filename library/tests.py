class Tester:
    def __init__(self, shiro):
        self.shiro = shiro

    async def run(self):
        """Start tests"""
        await self.test_commands()

    async def test_commands(self):
        """Run tests for every command"""
        for command in self.shiro.walk_commands():
            pass
