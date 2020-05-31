from discord.ext import commands
from database import Database

import uuid

from datetime import datetime, timedelta


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
        data = db.fetchone()

        if data:
            if datetime.strptime(data[2], "%Y-%m-%d %H:%M:%S.%f") < (datetime.now() - timedelta(days=1)):
                db.delete(table="register_requests", discord_id=ctx.author.id)
            else:
                await ctx.send(
                    "Bir önceki katılma isteğinizin süresi dolmadı. Lütfen DM'deki geçerli linke tıklayınız.")
                return

        key = uuid.uuid4().hex[:32]
        db.insert("register_requests", ctx.author.id, key, datetime.now())

        cfg = Database.get_config()

        try:
            await ctx.author.send(
                "Kaydınızı tamamlamak için " + cfg[
                    "website"] + "/completeRegistration?key=" + key + " adresinden osu! hesabınızı tanımlayın! Bu link yalnızca 24 saatliğine geçerlidir.")
        except:
            db.delete(table="register_requests", discord_id=ctx.author.id)
            await ctx.send("DM göndermede hata oluştu. Lütfen gizlilik ayarlarınızdan DM izinlerinizi kontrol edin.")
            return
        await ctx.send("Kaydınızı tamamlamak için lütfen DM'nize gelen linke tıklayın.")

    @commands.command(name='leave')
    async def exit_tourney(self, ctx):
        """
        Turnuvadan ayrıl.
        """
        db = Database()
        db.select(table="users", discord_id=ctx.author.id)
        if db.fetchone():
            db.delete(table="users", discord_id=ctx.author.id)
            await ctx.send("Turnuvadan başarıyla çıkış yaptınız.")
        else:
            await ctx.send("Turnuvada kayıtlı değilsiniz.")


def setup(bot):
    bot.add_cog(Registrations(bot))
