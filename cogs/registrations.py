from discord.ext import commands
from database import Database

import uuid
import json

from datetime import datetime, timedelta


class Registrations(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def leave_from_all_lobbies(userid):
        db = Database()
        cursor = db.get_cursor()
        cursor.execute(
            "select lobbies.* from lobbies LEFT OUTER JOIN stages ON lobbies.stage = stages.stage WHERE stages.max_tb = 0")
        lobbies = cursor.fetchall()
        for lobby in lobbies:
            user_list = json.loads(lobby[1])
            if any(x['osu_id'] == userid for x in user_list):
                for x in range(len(user_list)):
                    if user_list[x - 1]['osu_id'] == userid:
                        del user_list[x - 1]
                cursor.execute("UPDATE lobbies SET players = ? WHERE id = ?",
                               (json.dumps(user_list), lobby[0],))
                db.commit()
                return True

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
        user = db.fetchone()
        if user:
            self.leave_from_all_lobbies(user[6])
            db.delete(table="users", discord_id=ctx.author.id)
            await ctx.send("Turnuvadan başarıyla çıkış yaptınız.")
        else:
            await ctx.send("Turnuvada kayıtlı değilsiniz.")


def setup(bot):
    bot.add_cog(Registrations(bot))
