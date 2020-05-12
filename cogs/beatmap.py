import discord
from discord.ext import commands
from database import Database

import json
import requests
from bs4 import BeautifulSoup
from oppai import ezpp_set_autocalc, ezpp_new, ezpp_data_dup, ezpp_set_mods, MODS_DT, MODS_HR, ezpp_stars, \
    ezpp_ar, ezpp_hp, ezpp_od, ezpp_cs


class Mappool(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def get_map_info(map_id):
        r = requests.get(f"https://osu.ppy.sh/b/{map_id}")
        soup = BeautifulSoup(r.text, 'html.parser')
        try:
            json_bmap = soup.find(id="json-beatmapset").string
        except:
            raise Exception(f"`{map_id}` id'li mapi osu!'da bulamadım.")
        bmap_dict = json.loads(json_bmap)

        try:
            osu_file = requests.get(f"https://bloodcat.com/osu/b/{map_id}")
        except:
            raise Exception(f"`{map_id}` bloodcat'te bulunamadı.")

        osu_file_contents = osu_file.content

        ezpp_map = ezpp_new()
        ezpp_set_autocalc(ezpp_map, 1)
        ezpp_data_dup(ezpp_map, osu_file_contents.decode('utf-8'), len(osu_file_contents))

        return bmap_dict, ezpp_map

    @commands.command(name='stage')
    @commands.has_permissions(administrator=True)
    async def stages(self, ctx, action, stage=None, max_nm=None, max_hd=None, max_hr=None, max_dt=None,
                     max_fm=None, max_tb=None, pool_override=None):
        """
        Add or remove a stage

        action: (add, remove, list)
        stage: Name of the stage
        max_nm: Maximum NM map count
        max_hd: Maximum HD map count
        max_hr: Maximum HR map count
        max_dt: Maximum DT map count
        max_fm: Maximum FM map count
        max_tb: Maximum TB map count
        pool_override: Use different stages mappool
        """
        if action.lower() == "add":
            if stage is None or max_nm is None or max_hd is None or max_hr is None or max_dt is None or max_fm is None or max_tb is None:
                await ctx.send('Please specify all parameters.')
                return
            if not max_nm.isnumeric() or not max_hd.isnumeric() or not max_hr.isnumeric() or not max_dt.isnumeric() or not max_fm.isnumeric() or not max_tb.isnumeric():
                await ctx.send('Please specify maximum values numerical.')
                return

            db = Database()
            db.select(table="stages", stage=stage)
            if db.fetchone():
                await ctx.send('Specified stage is already exist.')
                return

            if pool_override is not None:
                db.select(table="stages", mappool=pool_override)
                data = db.fetchone()
                if not data:
                    await ctx.send('Specified pool is not found.')
                    return
                max_nm = data[2]
                max_hd = data[3]
                max_hr = data[4]
                max_dt = data[5]
                max_fm = data[6]
                max_tb = data[7]
            else:
                pool_override = stage

            db.insert("stages", stage, pool_override, max_nm, max_hd, max_hr, max_dt, max_fm, max_tb)
            await ctx.send('Successfully added the stage {}.'.format(stage))
            return

        elif action.lower() == "remove":
            if stage is None:
                await ctx.send('Please specify the stage.')
                return
            db = Database()
            db.select("stages", stage=stage)
            if db.fetchone():
                db.delete("stages", stage=stage)
                await ctx.send('Successfully removed the stage.')
                return
            else:
                await ctx.send('Specified stage is not found.')
                return

        elif action.lower() == "list":
            db = Database()
            db.select("stages")
            data = db.fetchall()

            desc_text = ""

            for val in data:
                desc_text += "**" + val[0] + "** (" + val[1] + ")"
                desc_text += " ----------- "
                desc_text += "{}-{}-{}-{}-{}-{}".format(val[2], val[3], val[4], val[5], val[6], val[7])
                desc_text += "\n\n"

            color = discord.Color.from_rgb(40, 60, 90)
            embed = discord.Embed(description=desc_text, color=color)
            embed.set_author(name="Stage List")
            await ctx.send(embed=embed)
            return

        else:
            await ctx.send('Please specify your action! (add,remove,list)')
            return

    @commands.command(name='mappool')
    @commands.has_role("Mappool")
    async def mappool(self, ctx, action, map_link=None, pool=None, mod=None, comment=""):
        """
        Add, remove or show maps from the mappools
        action: "add", "remove"
        map_link: (Optional) Link of the map you want to add or remove
        pool: (Optional) Which week's pool do you want to add this map? (qf, w1, w2)
        mod: (Optional) Which mod pool is this map going to be added? (nm, hd, hr, dt, fm, tb)
        comment: (Optional) Comment about the beatmap ("slow finger control, bit of alt"). Should be in quotation marks. Can be empty
        """

        if action.lower() == "add":
            if map_link is None or pool is None or mod is None:
                await ctx.send('Please specify all parameters.')
                return

            mod = mod.upper()

            db = Database()
            db.select("stages", mappool=pool)
            data = db.fetchone()
            max_maps = [data[2], data[3], data[4], data[5], data[6], data[7]]

            if not data:
                await ctx.send("This mappool is not found.")
                return

            if not (map_link.startswith("http://") or map_link.startswith("https://")):
                await ctx.send(f"Map link should start with http:// or https://.\n"
                               f"You linked <{map_link}>, I don't think it's a valid link.")
                return

            map_id = map_link.split("/")[-1]
            try:
                map_id_int = int(map_id)
            except:
                await ctx.send(f"Map link seems wrong. Please check again. \n"
                               f"You linked <{map_link}> but I couldn\'t find beatmap id from it.")
                return

            mods = ["NM", "HD", "HR", "DT", "FM", "TB"]
            mod_index = mods.index(mod)

            if mod not in mods:
                await ctx.send(f"Mods can only be one of from {mods}.\n"
                               f"You wanted to select {mod} mod pool, but it does not exist.")
                return

            if db.count("beatmaps", map_id=map_id) != 0:
                await ctx.send(f"The map you linked has been used in the previous iterations of this tournament.\n"
                               f"You linked <{map_link}>")
                return

            map_info, ezpp_map = self.get_map_info(map_id)

            selected_bmap = None
            for bmap in map_info["beatmaps"]:
                if bmap["id"] == map_id_int:
                    selected_bmap = bmap
                    break

            if mod == "HR":
                ezpp_set_mods(ezpp_map, MODS_HR)
            elif mod == "DT":
                ezpp_set_mods(ezpp_map, MODS_DT)
                selected_bmap["hit_length"] = int(selected_bmap["hit_length"] // 1.5)
                selected_bmap["bpm"] = selected_bmap["bpm"] * 1.5
            stars = ezpp_stars(ezpp_map)

            bmapset_id = map_info["id"]
            bmap_artist = map_info["artist"]
            bmap_title = map_info["title"]
            bmap_cover = map_info["covers"]["cover"]
            bmap_url = selected_bmap["url"]
            bmap_version = selected_bmap["version"]

            map_name = f"{bmap_artist} - {bmap_title} [{bmap_version}]"

            max_map_in_pool = max_maps[mod_index]
            if db.count("beatmaps", modpool=mod, mappool=pool) >= max_map_in_pool:
                author_name = f"Couldn't add map to {pool} Pool - {mod}"
                title_text = map_name
                desc_text = "Map couldn't be added to the pool, because pool is full!"
                bmap_cover = ""
                footer_text = f"{max_map_in_pool} out of {max_map_in_pool} maps in {pool} {mod} pool"
            else:
                title_text = map_name
                author_name = f"Successfully added map to {pool} Pool - {mod}"
                desc_text = ""
                footer_text = f"{db.count('beatmaps', modpool=mod, mappool=pool) + 1} out of {max_map_in_pool} maps in {pool} {mod} pool"
                db.insert("beatmaps", map_id, bmapset_id, bmap_title, bmap_artist, ctx.author.name, comment, pool, mod, stars,
                          selected_bmap["bpm"], selected_bmap["hit_length"], ezpp_ar(ezpp_map), ezpp_cs(ezpp_map),
                          ezpp_od(ezpp_map), ezpp_hp(ezpp_map))

            embed = discord.Embed(title=title_text, description=desc_text,
                                  color=discord.Color.from_rgb(60,60,60), url=bmap_url)
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/520370557531979786/693448457154723881/botavatar.png")
            embed.set_author(name=author_name)
            embed.set_image(url=bmap_cover)
            embed.set_footer(text=footer_text)

            await ctx.send(embed=embed)
            return

        elif action.lower() == "remove":
            if map_link == "":
                await ctx.send('Please specify a beatmap link.')
                return

            if not (map_link.startswith("http://") or map_link.startswith("https://")):
                await ctx.send(f"Map link should start with http:// or https://.\n"
                               f"You linked <{map_link}>, I don't think it's a valid link.")
                return

            map_id = map_link.split("/")[-1]
            try:
                int(map_id)
            except:
                await ctx.send(f"Map link seems wrong. Please check again. \n"
                               f"You linked <{map_link}> but I couldn\'t find beatmap id from it.")
                return

            db = Database()

            if db.count("beatmaps", map_id=map_id) == 0:
                await ctx.send(f"The specified beatmap does not exist in the pools.\n"
                               f"You wanted to remove <{map_link}>.")
                return

            db.delete("beatmaps", map_id=map_id)
            await ctx.send(f"Successfully deleted <{map_link}> from pools.")

            return
        else:
            await ctx.send('Please specify your action! (add,remove)')


def setup(bot):
    bot.add_cog(Mappool(bot))
