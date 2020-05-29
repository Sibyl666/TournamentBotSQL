import discord
from discord.ext import commands

from datetime import datetime

from database import Database


class Matches(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='lobby')
    @commands.has_permissions(administrator=True)
    async def manage_lobby(self, ctx, action="", argv1=None, argv2=None, argv3=None, *date):
        """
        Add, remove, update or list lobbies.
        action: "add", "remove", "update" or "list"
        date: dd/mm HH:MM

        lobby add player1 player2 stage date
        lobby remove lobby_name
        lobby update lobby_name date
        lobby list
        """
        if action == "add":
            date = " ".join(date)
            player1 = argv1
            player2 = argv2
            stage = argv3
            if player1 is None or player2 is None:
                await ctx.send("Please specify all players.")
                return
            if stage is None:
                await ctx.send("Please specify the stage.")
                return
            if date is None:
                await ctx.send("Please specify date. (dd/mm HH:MM)")
                return

            stage = stage.upper()

            try:
                lobby_date = datetime.strptime(date, '%d/%m %H:%M')
            except:
                await ctx.send("Please specify date correctly. (dd/mm HH:MM)")
                return

            lobby_date = lobby_date.replace(year=2020)
            date_string = lobby_date.strftime("%d/%m/%Y - %H:%M, %a")

            db = Database()
            db.select("users", osu_username=player1)
            player1_details = db.fetchone()
            if not player1_details:
                await ctx.send("Please specify player 1 correctly.")
                return

            db.select("users", osu_username=player2)
            player2_details = db.fetchone()
            if not player2_details:
                await ctx.send("Please specify player 2 correctly.")
                return

            if db.count("stages", stage=stage) == 0:
                await ctx.send("Please specify an existing stage.")
                return

            lobby_id = db.likecount("lobbies", id=stage+"_%") + 1
            lobby = stage + "_" + str(lobby_id)

            db.insert("lobbies", lobby, player1_details[6], player2_details[6], None, None, date_string,
                      stage, None, None)

            await ctx.send("Successfully added the lobby {}.".format(lobby))

        elif action == "remove":
            lobby_id = argv1.upper()

            if argv1 is None:
                await ctx.send("Please specify the lobby name.")
                return

            db = Database()
            if db.count("lobbies", id=lobby_id) != 0:
                db.delete("lobbies", id=lobby_id)
                await ctx.send("Successfully removed lobby {}.".format(lobby_id))
                return
            else:
                await ctx.send("Please specify lobby name correctly.")
                return
        elif action == "update":
            lobby_id = argv1.upper()
            date = "{} {}".format(argv2, argv3)

            if lobby_id is None:
                await ctx.send("Please specify the lobby name.")
                return
            if argv2 is None or argv3 is None:
                await ctx.send("Please specify the date correctly.")
                return

            try:
                lobby_date = datetime.strptime(date, '%d/%m %H:%M')
            except:
                await ctx.send("Please specify date correctly. (dd/mm HH:MM)")
                return

            lobby_date = lobby_date.replace(year=2020)
            date_string = lobby_date.strftime("%d/%m/%Y - %H:%M, %a")

            db = Database()

            if db.count("lobbies", id=lobby_id) != 0:
                db.update("lobbies", where="id="+lobby_id, date=date_string)
                await ctx.send("Successfully updated lobby {} to {}.".format(lobby_id, date_string))
                return
            else:
                await ctx.send("Please specify lobby name correctly.")
                return
        elif action == "list":
            db = Database()
            db.select("lobbies")
            data = db.fetchall()

            desc_text = ""

            for val in data:
                db.select("users", osu_id=val[1])
                player1 = db.fetchone()
                db.select("users", osu_id=val[2])
                player2 = db.fetchone()

                ref = "None" if val[3] is None else discord.Client.get_user(self.bot, int(val[3])).name

                desc_text += "**" + val[0] + "** (" + val[6] + ") "
                desc_text += "{} vs {}".format(player1[5], player2[5])
                desc_text += " - "
                desc_text += "Ref: {}, Date: {}".format(ref, val[5])
                desc_text += "\n\n"

            color = discord.Color.from_rgb(*Database.get_config()["accent_color"])
            embed = discord.Embed(description=desc_text, color=color)
            embed.set_author(name="Stage List")
            await ctx.send(embed=embed)
            return
        else:
            await ctx.send('Please specify an action!')

    @commands.command("refmatch")
    @commands.has_role("Hakem")
    async def manage_ref_match(self, ctx, action, lobby_name):
        """
        Manage referees for match.
        action: "join", "leave"
        lobby_name: Matchs lobby name.
        """
        if action == "join":
            db = Database()
            lobby_name = lobby_name.upper()
            db.select("lobbies", id=lobby_name)
            lobby_data = db.fetchone()
            if not lobby_data:
                await ctx.send('Please specify lobby name correctly.')
                return

            if lobby_data[3] is not None:
                if lobby_data[3] == ctx.message.author.id:
                    await ctx.send("You have already joined this lobby.")
                    return
                else:
                    await ctx.send("Already {} joined this lobby.".format(discord.Client.get_user(
                        self.bot, int(lobby_data[3])).name))
                    return
            else:
                db.update("lobbies", where="id="+lobby_name, referee=ctx.message.author.id)
                await ctx.send("{} successfully joined the lobby {}.".format(ctx.message.author.name, lobby_name))
                return
        elif action == "leave":
            db = Database()
            lobby_name = lobby_name.upper()
            db.select("lobbies", id=lobby_name)
            lobby_data = db.fetchone()
            if not lobby_data:
                await ctx.send('Please specify lobby name correctly.')
                return

            if lobby_data[3] != str(ctx.message.author.id):
                await ctx.send('You have not joined this lobby.')
                return
            else:
                db.update("lobbies", where="id="+lobby_name, referee=None)
                await ctx.send('You have successfully left the lobby {}.'.format(lobby_name))
                return
        else:
            await ctx.send('Please specify an action!')
            return


def setup(bot):
    bot.add_cog(Matches(bot))
