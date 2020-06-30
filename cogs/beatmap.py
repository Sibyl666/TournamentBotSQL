import discord
from discord.ext import commands
from database import Database

from distutils import util
import cloudscraper
import json
import requests
from bs4 import BeautifulSoup
from oppai import ezpp_set_autocalc, ezpp_new, ezpp_data_dup, ezpp_set_mods, MODS_DT, MODS_HR, ezpp_stars, \
    ezpp_ar, ezpp_hp, ezpp_od, ezpp_cs

def in_channel(channel_id):
    def predicate(ctx):
        return ctx.message.channel.id == channel_id
    return commands.check(predicate)

class Mappool(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def get_map_info(map_id):
        scraper = cloudscraper.create_scraper()
        r = scraper.get(f"https://osu.ppy.sh/b/{map_id}")
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

    @staticmethod
    async def show_single_mod_pool(ctx, bmaps, which_pool, mod):

        color = discord.Color.from_rgb(*Database.get_config()["accent_color"])
        desc_text = ""
        for bmap in bmaps:
            bpm = float(bmap[12])
            length = int(bmap[13])
            star_rating = round(float(bmap[11]), 2)

            bmap_url = "https://osu.ppy.sh/b/{0}".format(bmap[0])
            bmap_name = f"{bmap[3]} - {bmap[2]} [{bmap[5]}]"
            desc_text += f"[{bmap_name}]({bmap_url})\n" \
                f"▸**Length:** {length // 60}:{length % 60:02d} ▸**BPM:** {bpm:.1f} ▸**SR:** {star_rating}* "
            if bmap[8] != "":
                desc_text += f"▸**C:** `{bmap[8]}`"
            desc_text += f"\n ▸**AR:** {round(float(bmap[15]), 2)} ▸**CS:** {round(float(bmap[16]), 2)} ▸**OD:** {round(float(bmap[17]), 2)}" \
                f"▸**HP:** {round(float(bmap[18]), 2)} \n" \
                f"▸**Mapper:** {bmap[4]} ▸**Status:** {bmap[6]} ▸**Max Combo:** x{bmap[14]}\n"

        author_name = f"Beatmaps in {which_pool} - {mod}"
        embed = discord.Embed(description=desc_text, color=color)
        embed.set_author(name=author_name)
        await ctx.send(embed=embed)

        return

    @commands.command(name='stage')
    @commands.has_permissions(administrator=True)
    async def stages(self, ctx, action, stage=None, max_nm=None, max_hd=None, max_hr=None, max_dt=None,
                     max_fm=None, max_tb=None, best_of=None, eliminate_when_lose=None , pool_override=None):
        """
        Add or remove a stage, or show stages.

        action: (add, remove, list)
        stage: Name of the stage
        max_nm: Maximum NM map count
        max_hd: Maximum HD map count
        max_hr: Maximum HR map count
        max_dt: Maximum DT map count
        max_fm: Maximum FM map count
        max_tb: Maximum TB map count
        best_of: Best of number
        eliminate_when_lose: true or false, eliminates player when lost the match.
        pool_override: Use different stages mappool
        """
        if action.lower() == "add":
            if stage is None or max_nm is None or max_hd is None or max_hr is None or max_dt is None or max_fm is None or max_tb is None or best_of is None or eliminate_when_lose is None:
                await ctx.send('Please specify all parameters.')
                return
            if not max_nm.isnumeric() or not max_hd.isnumeric() or not max_hr.isnumeric() or not max_dt.isnumeric() or not max_fm.isnumeric() or not max_tb.isnumeric() or not best_of.isnumeric():
                await ctx.send('Please specify maximum values numerical.')
                return

            try:
                eliminate_when_lose = bool(util.strtobool(eliminate_when_lose))
            except:
                await ctx.send('Please specify eliminate when lose correctly (true/false).')
                return

            stage = stage.upper()

            db = Database()
            db.select(table="stages", stage=stage)
            if db.fetchone():
                await ctx.send('Specified stage is already exist.')
                return

            if pool_override is not None:
                pool_override = pool_override.upper()
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
                best_of = data[8]
            else:
                pool_override = stage

            db.insert("stages", stage, pool_override, max_nm, max_hd, max_hr, max_dt, max_fm, max_tb, best_of, False, eliminate_when_lose)
            await ctx.send('Successfully added the stage {}.'.format(stage))
            return

        elif action.lower() == "remove":
            if stage is None:
                await ctx.send('Please specify the stage.')
                return
            stage = stage.upper()
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
                desc_text += "**" + val[0] + "** (" + val[1] + ") BO: `{}` E: `{}`".format(val[8], bool(val[10]))
                desc_text += " → "
                desc_text += "NM: `{}` HD: `{}` HR: `{}` DT: `{}` FM: `{}` TB: `{}`"\
                    .format(val[2], val[3], val[4], val[5], val[6], val[7])
                desc_text += "\n\n"

            color = discord.Color.from_rgb(*Database.get_config()["accent_color"])
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
        Add or remove maps from the mappools.
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
            pool = pool.upper()

            db = Database()
            db.select("stages", mappool=pool)
            data = db.fetchone()

            if not data:
                await ctx.send("This mappool is not found.")
                return

            max_maps = [data[2], data[3], data[4], data[5], data[6], data[7]]

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

            if mod not in mods:
                await ctx.send(f"Mods can only be one of from {mods}.\n"
                               f"You wanted to select {mod} mod pool, but it does not exist.")
                return

            mod_index = mods.index(mod)

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
            bmapset_creator = map_info["creator"]
            bmap_artist = map_info["artist"]
            bmap_title = map_info["title"]
            bmap_cover = map_info["covers"]["cover"]
            bmap_url = selected_bmap["url"]
            bmap_approved = selected_bmap["status"].capitalize()
            bmap_version = selected_bmap["version"]
            bmap_maxcombo = selected_bmap["max_combo"]

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
                db.insert("beatmaps", map_id, bmapset_id, bmap_title, bmap_artist, bmapset_creator, bmap_version,
                          bmap_approved, ctx.author.name, comment, pool, mod, stars, selected_bmap["bpm"],
                          selected_bmap["hit_length"], bmap_maxcombo, ezpp_ar(ezpp_map), ezpp_cs(ezpp_map),
                          ezpp_od(ezpp_map), ezpp_hp(ezpp_map))

            embed = discord.Embed(title=title_text, description=desc_text,
                                  color=discord.Color.from_rgb(*Database.get_config()["accent_color"]), url=bmap_url)
            embed.set_thumbnail(
                url="https://112ninturnuvalari.xyz/embed.png")
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


    @commands.command(name='poolshow')
    @commands.has_role("Mappool")
    @in_channel(723997874873958451)
    async def mappool_show(self, ctx, which_pool, mod=None):
        """
        Shows the selected pool.
        which_pool: Pool that will be shown
        mod: (Optional) Can be one of [NM, HD, HR, DT, FM, TB], if not given, bot will display all the maps in the pool
        """
        db = Database()

        which_pool = which_pool.upper()
        db.select("stages", mappool=which_pool)
        stage = db.fetchone()

        if not stage:
            await ctx.send("Specified mappool is not found.")
            return

        mods = ["NM", "HD", "HR", "DT", "FM", "TB"]

        for i in range(2, 8):
            if stage[i] == 0:
                del mods[i-2]

        show_all = False
        if mod is None:
            show_all = True
        else:
            mod = mod.upper()
            if mod not in mods:
                await ctx.send(f"Mods can only be one of from {mods}.\n"
                            f"You wanted to select {mod} mod pool, but it does not exist.")
                return

        if show_all:
            for mod in mods:
                db.select("beatmaps", mappool=which_pool, modpool=mod)
                bmaps = db.fetchall()

                await self.show_single_mod_pool(ctx, bmaps, which_pool, mod)
        else:
            db.select("beatmaps", mappool=which_pool, modpool=mod)
            bmaps = db.fetchall()
            await self.show_single_mod_pool(ctx, bmaps, which_pool, mod)

        return

    @commands.command(name='announcepool')
    @commands.has_permissions(administrator=True)
    async def announce_pool(self, ctx, mappool):
        """
        Announce or hide mappools.

        mappool: Mappool's id.
        """
        mappool = mappool.upper()

        db = Database()
        db.select("stages", mappool=mappool)
        stage = db.fetchone()

        if not stage:
            await ctx.send("Specified mappool is not found.")
            return

        if stage[8] == 1:
            db.update("stages", where="mappool="+mappool, showmappool=False)
            await ctx.send("Successfully hid the pool {}.".format(mappool))
            return
        else:
            db.update("stages", where="mappool="+mappool, showmappool=True)
            await ctx.send("Successfully announced the pool {}.".format(mappool))
            return


def setup(bot):
    bot.add_cog(Mappool(bot))
