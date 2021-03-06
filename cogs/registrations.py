import discord
from discord.ext import commands
from database import Database
import asyncio

import uuid
import json

from datetime import datetime, timedelta


class Registrations(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def player_role_task(self):
        await self.bot.wait_until_ready()
        db = Database()
        while self.bot.is_closed:
            guild = self.bot.get_guild(db.get_config()["guild_id"])
            player_role = discord.utils.get(guild.roles, id=db.get_config()["player_role_id"])
            db.select("users", eliminated=False)
            active_players = db.fetchall()
            try:
                for member in guild.members:
                    if player_role in member.roles:
                        if not any(p[0] == member.id for p in active_players):
                            print(f"Removing role from: {member}")
                            await member.remove_roles(player_role)
                    else:
                        if any(p[0] == member.id for p in active_players):
                            print(f"Giving role to: {member}")
                            await member.add_roles(player_role)
            except Exception as e:
                print(e)
            await asyncio.sleep(30)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self.player_role_task())

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

        await ctx.send("Turnuvaya Kayıtlar 30 Temmuz'da kapandı.")

        # db = Database()
        # db.select(table="users", discord_id=ctx.author.id)
        # if db.fetchone():
        #     await ctx.send("Turnuvaya zaten kayıtlısın.")
        #     return

        # db.select(table="register_requests", discord_id=ctx.author.id)
        # data = db.fetchone()

        # if data:
        #     if datetime.strptime(data[2], "%Y-%m-%d %H:%M:%S.%f") < (datetime.now() - timedelta(days=1)):
        #         db.delete(table="register_requests", discord_id=ctx.author.id)
        #     else:
        #         await ctx.send(
        #             "Bir önceki katılma isteğinizin süresi dolmadı. Lütfen DM'deki geçerli linke tıklayınız.")
        #         return

        # key = uuid.uuid4().hex[:32]
        # db.insert("register_requests", ctx.author.id, key, datetime.now())

        # cfg = Database.get_config()

        # try:
        #     await ctx.author.send(
        #         "Kaydınızı tamamlamak için " + cfg[
        #             "website"] + "/completeRegistration?key=" + key + " adresinden osu! hesabınızı tanımlayın! Bu link yalnızca 24 saatliğine geçerlidir.")
        # except:
        #     db.delete(table="register_requests", discord_id=ctx.author.id)
        #     await ctx.send("DM göndermede hata oluştu. Lütfen gizlilik ayarlarınızdan DM izinlerinizi kontrol edin.")
        #     return
        # await ctx.send("Kaydınızı tamamlamak için lütfen DM'nize gelen linke tıklayın.")

    @commands.has_permissions(administrator=True)
    @commands.command(name='lobbykick')
    async def lobby_kick(self, ctx, user):
        """
        Oyuncuyu qualifier lobilerinden çıkar.

        user: Kullanıcının osu adı veya discorddan etiketlenmiş hali.
        """
        if user.startswith("<@!"):
            player = discord.Client.get_user(self.bot,
                                             int(user.replace("<", "").replace("!", "")
                                                 .replace(">", "").replace("@", "")))
            db = Database()
            db.select("users", discord_id=player.id)
            player_db = db.fetchone()
            if player_db:
                self.leave_from_all_lobbies(player_db[6])
                await ctx.send('Successfully removed {0} from all lobbies!'.format(player.name))
                return
            else:
                await ctx.send('{0} is not in tourney!'.format(player.name))
                return
        else:
            db = Database()
            db.select("users", osu_username=user)
            player_db = db.fetchone()
            if not player_db:
                await ctx.send('{0} is not in tourney!'.format(user))
                return
            else:
                self.leave_from_all_lobbies(player_db[6])
                await ctx.send('Successfully removed {0} from all lobbies!'.format(user))
                return

    @commands.has_permissions(administrator=True)
    @commands.command(name='kickuser')
    async def kick_user(self, ctx, user):
        """
        Turnuvadan oyuncu at.

        user: Kullanıcının osu adı veya discorddan etiketlenmiş hali.
        """
        if user.startswith("<@!"):
            player = discord.Client.get_user(self.bot,
                                             int(user.replace("<", "").replace("!", "")
                                                 .replace(">", "").replace("@", "")))
            db = Database()
            db.select("users", discord_id=player.id)
            player_db = db.fetchone()
            if player_db:
                self.leave_from_all_lobbies(player_db[6])
                db.delete("users", discord_id=player.id)
                await ctx.send('Successfully removed {0} from tourney!'.format(player.name))
                return
            else:
                await ctx.send('{0} is not in tourney!'.format(player.name))
                return
        else:
            db = Database()
            db.select("users", osu_username=user)
            player_db = db.fetchone()
            if not player_db:
                await ctx.send('{0} is not in tourney!'.format(user))
                return
            else:
                self.leave_from_all_lobbies(player_db[6])
                db.delete("users", osu_username=user)
                await ctx.send('Successfully removed {0} from tourney!'.format(user))
                return

    @commands.command(name='leave')
    async def exit_tourney(self, ctx):
        """
        Turnuvadan ayrıl.
        """

        await ctx.send("Turnuvadan çıkışlar kapandı.")

        # db = Database()
        # db.select(table="users", discord_id=ctx.author.id)
        # user = db.fetchone()
        # if user:
        #     self.leave_from_all_lobbies(user[6])
        #     db.delete(table="users", discord_id=ctx.author.id)
        #     await ctx.send("Turnuvadan başarıyla çıkış yaptınız.")
        # else:
        #     await ctx.send("Turnuvada kayıtlı değilsiniz.")


def setup(bot):
    bot.add_cog(Registrations(bot))
