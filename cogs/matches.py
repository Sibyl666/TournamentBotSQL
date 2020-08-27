import discord
from discord.ext import commands

from datetime import datetime
import json
import asyncio
import math
from pytz import timezone

from database import Database


class Matches(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def lobby_announcement_task(self):
        await self.bot.wait_until_ready()
        db = Database()
        channel = self.bot.get_channel(db.get_config()["announcement_channel"])
        while self.bot.is_closed:
            db.select("lobbies")
            lobbies = db.fetchall()
            try:
                for lobby in [l for l in lobbies if l[6] is None]:
                    lobbydate = datetime.strptime(lobby[4], "%d/%m/%Y - %H:%M, %a")
                    players = json.loads(lobby[1])
                    now = datetime.now(timezone("Europe/Istanbul")).replace(tzinfo=None)
                    if math.ceil((lobbydate - now).total_seconds() / 60) == 15:
                        print(f"Announcing lobby {lobby[0]}.")
                        ref = "<@{}>".format(lobby[2]) if lobby[2] is not None else "-"
                        player_mention_array = []
                        for player in players:
                            player_mention_array.append("<@{}>".format(player["discord_id"]))
                        await channel.send('**{}** - {} lobisi için son 15 dakika kaldı! Hakem: {}'.format(
                            lobby[0], ", ".join(player_mention_array), ref
                        ))
            except Exception as e:
                print(e)
            await asyncio.sleep(60)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self.lobby_announcement_task())

    @commands.command(name='lobby')
    @commands.has_permissions(administrator=True)
    async def manage_lobby(self, ctx, action="", *args):
        """
        Add, remove, update or list lobbies.
        action: "add", "remove", "update" or "list"
        date: dd/mm HH:MM

        lobby add stage player1 player2 date
        lobby add stage date (for qualifier stages)

        lobby remove lobby_name
        lobby update lobby_name date
        lobby list
        """
        if action == "add":

            if len(args) < 1:
                await ctx.send("Please specify the stage.")
                return

            stage = args[0]
            stage = stage.upper()

            db = Database()
            db.select("stages", stage=stage)
            stage_details = db.fetchone()

            if not stage_details:
                await ctx.send("Please specify the state correctly.")
                return

            if stage_details[7] == 0:
                if len(args) < 3:
                    await ctx.send("Please specify date. (dd/mm HH:MM)")
                    return

                date = " ".join([args[1], args[2]])

                try:
                    lobby_date = datetime.strptime(date, '%d/%m %H:%M')
                except:
                    await ctx.send("Please specify date correctly. (dd/mm HH:MM)")
                    return

                lobby_date = lobby_date.replace(year=2020)
                date_string = lobby_date.strftime("%d/%m/%Y - %H:%M, %a")

                # lobby_id = db.likecount("lobbies", id=stage + "_%") + 1
                lobby = stage + "_" + str(db.get_next_id("lobbies", stage))

                db.insert("lobbies", lobby, json.dumps([]), None, None, date_string,
                          stage, None, None)

                await ctx.send("Successfully added the lobby {}.".format(lobby))

                return
            else:
                if len(args) < 3:
                    await ctx.send("Please specify all players.")
                    return
                if len(args) < 5:
                    await ctx.send("Please specify date. (dd/mm HH:MM)")
                    return

                player1 = args[1]
                player2 = args[2]
                date = " ".join([args[3], args[4]])

                try:
                    lobby_date = datetime.strptime(date, '%d/%m %H:%M')
                except:
                    await ctx.send("Please specify date correctly. (dd/mm HH:MM)")
                    return

                lobby_date = lobby_date.replace(year=2020)
                date_string = lobby_date.strftime("%d/%m/%Y - %H:%M, %a")

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

                player1 = {
                    "osu_id": player1_details[6],
                    "osu_username": player1_details[5],
                    "discord_id": player1_details[0]
                }

                player2 = {
                    "osu_id": player2_details[6],
                    "osu_username": player2_details[5],
                    "discord_id": player2_details[0]
                }

                players = [player1, player2]

                # lobby_id = db.likecount("lobbies", id=stage+"_%") + 1
                lobby = stage + "_" + str(db.get_next_id("lobbies", stage))

                db.insert("lobbies", lobby, json.dumps(players), None, None, date_string,
                          stage, None, None)

                await ctx.send("Successfully added the lobby {}.".format(lobby))

        elif action == "remove":
            if len(args) < 1:
                await ctx.send("Please specify the lobby name.")
                return

            lobby_id = args[0].upper()

            db = Database()
            if db.count("lobbies", id=lobby_id) != 0:
                db.delete("lobbies", id=lobby_id)
                await ctx.send("Successfully removed lobby {}.".format(lobby_id))
                return
            else:
                await ctx.send("Please specify lobby name correctly.")
                return
        elif action == "update":
            if len(args) < 1:
                await ctx.send("Please specify the lobby name.")
                return
            if len(args) < 3:
                await ctx.send("Please specify the date correctly.")
                return

            lobby_id = args[0].upper()
            date = "{} {}".format(args[1], args[2])

            try:
                lobby_date = datetime.strptime(date, '%d/%m %H:%M')
            except:
                await ctx.send("Please specify date correctly. (dd/mm HH:MM)")
                return

            lobby_date = lobby_date.replace(year=2020)
            date_string = lobby_date.strftime("%d/%m/%Y - %H:%M, %a")

            db = Database()

            db.select("lobbies", id=lobby_id)
            lobby = db.fetchone()
            if lobby:
                db.update("lobbies", where="id=" + lobby_id, date=date_string)
                await ctx.send("Successfully updated lobby {} to {}.".format(lobby_id, date_string))
                if lobby[2] is not None:
                    await ctx.send("Referee <@{}>, the lobby date has been changed. If you cannot ref this lobby, you can leave this lobby.".format(lobby[2]))
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

                players_json = json.loads(val[1])
                separator = " vs "
                db.select("stages", stage=val[5])
                stagedata = db.fetchone()
                if stagedata[7] == 0:
                    separator = ","

                player_string = "No players"
                if len(players_json) > 0:
                    player_string = separator.join([v["osu_username"] for v in players_json])

                ref = "None" if val[2] is None else discord.Client.get_user(self.bot, int(val[2])).name

                desc_text += "**" + val[0] + "** (" + val[5] + ") "
                desc_text += player_string
                desc_text += " - "
                desc_text += "Ref: {}, Date: {}".format(ref, val[4])
                desc_text += "\n\n"

            color = discord.Color.from_rgb(*Database.get_config()["accent_color"])
            embed = discord.Embed(description=desc_text, color=color)
            embed.set_author(name="Lobby List")
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

            if lobby_data[2] is not None:
                if lobby_data[2] == ctx.message.author.id:
                    await ctx.send("You have already joined this lobby.")
                    return
                else:
                    await ctx.send("Already {} joined this lobby.".format(discord.Client.get_user(
                        self.bot, int(lobby_data[2])).name))
                    return
            else:
                db.update("lobbies", where="id=" + lobby_name, referee=ctx.message.author.id)
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

            if lobby_data[2] != str(ctx.message.author.id):
                await ctx.send('You have not joined this lobby.')
                return
            else:
                db.update("lobbies", where="id=" + lobby_name, referee=None)
                await ctx.send('You have successfully left the lobby {}.'.format(lobby_name))
                return
        else:
            await ctx.send('Please specify an action!')
            return

    @commands.command("eliminatequal")
    @commands.has_permissions(administrator=True)
    async def eliminate_qual_stage(self, ctx, stage=None, top=None):
        """
        Eliminates players for qualifier's average rankings.

        stage: qualifier stage.
        top: keep top x players to continue tournament.
        Please be careful for writing parameters correctly.
        """

        if stage is None or top is None:
            await ctx.send("Please specify all parameters.")
            return

        if not top.isnumeric():
            await ctx.send("Please specify top players as number.")
            return

        top = int(top)

        db = Database()
        db.select("stages", stage=stage, bestof=0)
        stage_details = db.fetchone()
        if not stage_details:
            await ctx.send("Please specify stage correctly.")
            return

        stage_scores = {}
        map_ranks = {}
        db.select("beatmaps", mappool=stage_details[1])
        for bmap in db.fetchall():
            stage_scores[str(bmap[0])] = {}
            map_ranks[str(bmap[0])] = []

        db.likeselect("scores", lobby_id=stage + "_%")
        lobbies = db.fetchall()
        for lobby in lobbies:
            lobby_scores = json.loads(lobby[2])
            for player in lobby_scores.keys():
                for bmap in lobby_scores[player].keys():
                    stage_scores[bmap][player] = lobby_scores[player][bmap]

        ranking_sum = {}
        for bmap in map_ranks.keys():
            for player in stage_scores[bmap].keys():
                map_ranks[bmap].append(player)
            map_ranks[bmap].sort(key=lambda x: stage_scores[bmap][x], reverse=True)

        for bmap in map_ranks.keys():
            for player in map_ranks[bmap]:
                if player not in ranking_sum:
                    ranking_sum[player] = 0
                ranking_sum[player] += map_ranks[bmap].index(player)

        ranking = list(ranking_sum.keys())
        ranking.sort(key=lambda x: ranking_sum[x])

        for player in ranking[top:]:
            db.update("users", where="osu_id="+player, eliminated=True)

        await ctx.send("Elimination successful.")


def setup(bot):
    bot.add_cog(Matches(bot))
