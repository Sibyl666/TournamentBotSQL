from discord.ext import commands
import discord
from database import Database

import cloudscraper
from bs4 import BeautifulSoup
import json


class Staff(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def get_osu_user(username):
        scraper = cloudscraper.create_scraper()
        r = scraper.get(f"https://osu.ppy.sh/u/{username}")
        soup = BeautifulSoup(r.text, 'html.parser')
        try:
            json_user = json.loads(soup.find(id="json-user").string)
            return json_user
        except:
            return False

    @commands.command(name='staff')
    @commands.has_permissions(administrator=True)
    async def manage_staff(self, ctx, action, *args):
        """
        Yetkili ekle/sil/listele/düzenle.

        action: add, remove, list, edit

        staff add @staff osu_username ...perms
        staff remove @staff | staff remove osu_username
        staff list
        staff edit @staff ...perms | staff edit osu_username ...perms

        Perms: host, hakem
        """
        if action == "add":
            if len(args) < 1:
                await ctx.send('Please mention staff from discord!')
                return
            if len(args) < 2:
                await ctx.send('Please specify osu username of staff!')
                return
            if len(args) < 3:
                await ctx.send('Please specify permissions of staff!')
                return

            if "<" not in args[0] or "@" not in args[0] or ">" not in args[0] or "!" not in args[0]:
                await ctx.send('Please mention staff correctly.')
                return

            if self.get_osu_user(args[1]) is False:
                await ctx.send('Please specify osu username correctly.')
                return

            staff_discord = discord.Client.get_user(self.bot,
                                                    int(args[0].replace("<", "")
                                                        .replace(">", "").replace("!", "").replace("@", "")))

            osu_id = self.get_osu_user(args[1])["id"]

            db = Database()
            db.select("staff", discord_id=staff_discord.id)
            if db.fetchone():
                await ctx.send("{} is already a staff.".format(staff_discord.name))
                return

            db.select("staff", osu_id=osu_id)
            if db.fetchone():
                await ctx.send("{} is already a staff.".format(args[1]))
                return

            perms = []

            for arg in args[2:]:
                if arg.lower() == "hakem" or arg.lower() == "host":
                    perms.append(arg.lower())
                else:
                    await ctx.send('Please specify permissions correctly.')
                    return

            db.insert("staff", staff_discord.id, osu_id, json.dumps(perms), args[1])
            await ctx.send('Successfully added {0} as staff!'.format(staff_discord.name))
            return
        elif action == "remove":
            if len(args) < 1:
                await ctx.send('Please specify the staff!')
                return

            staff = args[0]

            if staff.startswith("<@!"):
                staff = discord.Client.get_user(self.bot,
                                                int(staff.replace("<", "").replace("!", "")
                                                    .replace(">", "").replace("@", "")))
                db = Database()
                db.select("staff", discord_id=staff.id)
                if db.fetchone():
                    db.delete("staff", discord_id=staff.id)
                    await ctx.send('Successfully removed {0} from staff!'.format(staff.name))
                    return
                else:
                    await ctx.send('{0} is not staff!'.format(staff.name))
                    return
            else:
                if self.get_osu_user(staff) is False:
                    await ctx.send('Please specify staff correctly.')
                    return
                else:
                    staff = self.get_osu_user(staff)["id"]
                    db = Database()
                    db.select("staff", osu_id=staff)
                    if db.fetchone():
                        db.delete("staff", osu_id=staff)
                        await ctx.send('Successfully removed {0} from staff!'.format(args[0]))
                        return
                    else:
                        await ctx.send('{0} is not staff!'.format(args[0]))
                        return
        elif action == "list":
            db = Database()
            db.select("staff")
            data = db.fetchall()

            desc_text = ""

            for val in data:
                staff_discord = discord.Client.get_user(self.bot, val[0])
                staff_osu = self.get_osu_user(val[1])
                desc_text += "**" + staff_discord.name + "#" + staff_discord.discriminator \
                             + "** (" + staff_osu["username"] + ")"
                desc_text += " → "
                desc_text += "`{}`" \
                    .format(",".join([v for v in json.loads(val[2])]))
                desc_text += "\n\n"

            color = discord.Color.from_rgb(*Database.get_config()["accent_color"])
            embed = discord.Embed(description=desc_text, color=color)
            embed.set_author(name="Staff List")
            await ctx.send(embed=embed)
            return
        elif action == "edit":
            if len(args) < 1:
                await ctx.send('Please specify the staff!')
                return

            if len(args) < 2:
                await ctx.send('Please specify the permissions!')
                return

            staff = args[0]

            if staff.startswith("<@!"):
                staff = discord.Client.get_user(self.bot,
                                                int(staff.replace("<", "").replace("!", "")
                                                    .replace(">", "").replace("@", "")))
                db = Database()
                db.select("staff", discord_id=staff.id)
                if db.fetchone():
                    perms = []
                    for arg in args[1:]:
                        if arg.lower() == "hakem" or arg.lower() == "host":
                            perms.append(arg.lower())
                        else:
                            print(arg)
                            await ctx.send('Please specify permissions correctly.')
                            return
                    db.update("staff", where="discord_id=" + str(staff.id), perms=json.dumps(perms))
                    await ctx.send('Successfully updated {0}!'.format(staff.name))
                else:
                    await ctx.send('{0} is not staff!'.format(staff.name))
                    return
            else:
                if self.get_osu_user(staff) is False:
                    await ctx.send('Please specify staff correctly.')
                    return
                else:
                    staff = self.get_osu_user(staff)["id"]
                    db = Database()
                    db.select("staff", osu_id=staff)
                    if db.fetchone():
                        perms = []
                        for arg in args[1:]:
                            if arg.lower() == "hakem" or arg.lower() == "host":
                                perms.append(arg.lower())
                            else:
                                print(arg)
                                await ctx.send('Please specify permissions correctly.')
                                return
                        db.update("staff", where="osu_id="+str(staff), perms=json.dumps(perms))
                        await ctx.send('Successfully updated {0}!'.format(args[0]))
                        return
                    else:
                        await ctx.send('{0} is not staff!'.format(args[0]))
                        return
        else:
            await ctx.send('Please specify your action! (add,remove,list,edit)')
            return


def setup(bot):
    bot.add_cog(Staff(bot))
