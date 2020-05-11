from discord.ext import commands
from database import Database

import uuid

import datetime

import json


class Registrations(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='register')
    async def register_tourney(self, ctx):
        """
        Turnuvaya katılmak için istek oluştur.
        """
        db = Database()
        db.select(table="users", discord_id=ctx.author.id)
        if db.fetchone():
            await ctx.send("Turnuvaya zaten kayıtlısın.")
            return

        db.select(table="register_requests", discord_id=ctx.author.id)
        if db.fetchone():
            db.delete(table="register_requests", discord_id=ctx.author.id)

        key = uuid.uuid4().hex[:32]
        db.insert("register_requests", ctx.author.id, key, datetime.datetime.now())

        with open('config.json') as config_file:
            data = json.load(config_file)

        try:
            await ctx.author.send(
                "Kaydınızı tamamlamak için " + data["website"] + "/completeRegistration?key=" + key + " adresinden osu! hesabınızı tanımlayın! Bu link yalnızca 24 saatliğine geçerlidir.")
        except:
            await ctx.send("DM göndermede hata oluştu. Lütfen gizlilik ayarlarınızdan DM izinlerinizi kontrol edin.")
            return
        await ctx.send("Kaydınızı tamamlamak için lütfen DM'nize gelen linke tıklayın.")


def setup(bot):
    bot.add_cog(Registrations(bot))
