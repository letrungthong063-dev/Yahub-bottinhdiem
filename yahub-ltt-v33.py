import discord
from discord import app_commands
import aiohttp
import json
import os
import time
import asyncio
import importlib
import logging
from datetime import datetime, timezone, timedelta

# ================= LOGGING =================

class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG":    "\033[37m",
        "INFO":     "\033[36m",
        "WARNING":  "\033[33m",
        "ERROR":    "\033[31m",
        "CRITICAL": "\033[35m",
    }
    TAGS = {
        "[BXH]":      "\033[32m",
        "[ENABLE]":   "\033[32m",
        "[DISABLE]":  "\033[31m",
        "[GRANT]":    "\033[32m",
        "[REVOKE]":   "\033[31m",
        "[COOLDOWN]": "\033[33m",
        "[PUBLIC]":   "\033[32m",
        "[PRIVATE]":  "\033[31m",
    }
    RESET = "\033[0m"
    GRAY  = "\033[90m"
    BOLD  = "\033[1m"

    def format(self, record):
        time_str    = f"{self.GRAY}{self.formatTime(record, '%d/%m/%Y %H:%M:%S')}{self.RESET}"
        level_color = self.COLORS.get(record.levelname, self.RESET)
        level_str   = f"{level_color}{self.BOLD}[{record.levelname}]{self.RESET}"
        msg = record.getMessage()
        for tag, color in self.TAGS.items():
            if msg.startswith(tag):
                msg = f"{color}{self.BOLD}{tag}{self.RESET} {msg[len(tag)+1:]}"
                break
        return f"{time_str} {level_str} {msg}"

handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter())
logging.root.handlers = []
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)
logger = logging.getLogger("yahub-bot")

# ================= CONFIG =================

# Đọc từ file .env (nếu có) hoặc từ environment variables (Render)
def load_env(path=".env"):
    env = {}
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env[key.strip()] = value.strip()
        logger.info("Đã load cấu hình từ file .env")
    else:
        logger.info("Không có file .env, dùng environment variables")
    return env

env = load_env()

def get_env(key, default=""):
    return os.environ.get(key) or env.get(key, default)

TOKEN = get_env("TOKEN")
CLIENT_ID = get_env("CLIENT_ID")
BOT_OWNERS = [uid.strip() for uid in get_env("BOT_OWNERS").split(",") if uid.strip()]
COOKIE = get_env("COOKIE")

if not TOKEN:
    logger.error("Thiếu TOKEN trong file .env!")
    exit(1)
if not COOKIE:
    logger.error("Thiếu COOKIE trong file .env!")
    exit(1)

logger.info("Đã load cấu hình từ .env")

headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://congdong.ff.garena.vn",
    "Referer": "https://congdong.ff.garena.vn/tinh-diem",
    "Accept": "application/json, text/plain",
    "X-Requested-With": "XMLHttpRequest",
    "Cookie": COOKIE
}

# ================= FILE LOAD =================

if not os.path.exists("permissions.json"):
    with open("permissions.json", "w") as f:
        json.dump({}, f)

if not os.path.exists("logs.json"):
    with open("logs.json", "w") as f:
        json.dump([], f)

with open("permissions.json", "r") as f:
    permissions = json.load(f)

with open("logs.json", "r") as f:
    logs = json.load(f)

def save_permissions():
    with open("permissions.json", "w") as f:
        json.dump(permissions, f, indent=2)

def save_logs():
    with open("logs.json", "w") as f:
        json.dump(logs, f, indent=2)

def log_action(data):
    data["time"] = datetime.now(timezone.utc).isoformat()
    logs.append(data)
    save_logs()

# ================= BACKGROUNDS =================

def get_available_backgrounds():
    if not os.path.exists("backgrounds"):
        return []
    return [
        f.replace(".png", "")
        for f in os.listdir("backgrounds")
        if f.endswith(".png") and os.path.exists(f"renderers/{f.replace('.png', '')}.py")
    ]

def render_image(bg_name, leaderboard, start_str, name_str, logo_bytes, logo_map={}):
    try:
        importlib.invalidate_caches()
        renderer = importlib.import_module(f"renderers.{bg_name}")
        return renderer.create_image(leaderboard, start_str, name_str, logo_bytes, logo_map)
    except ModuleNotFoundError:
        raise FileNotFoundError(f"❌ Không tìm thấy background: `{bg_name}`")

# ================= BOT =================

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
cooldowns = {}
bot_start_time = time.time()

def convert_to_timestamp(date_str):
    VN_TZ = timezone(timedelta(hours=7))
    dt = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
    dt = dt.replace(tzinfo=VN_TZ)
    return int(dt.timestamp())

async def cleanup_cooldowns():
    while True:
        await asyncio.sleep(300)  # Dọn mỗi 5 phút
        now = time.time()
        expired = [k for k, v in cooldowns.items() if now > v]
        for k in expired:
            del cooldowns[k]
        if expired:
            logger.info(f"Đã dọn {len(expired)} cooldown hết hạn")

@client.event
async def on_ready():
    await tree.sync()
    bgs = get_available_backgrounds()
    logger.info(f"Bot online: {client.user} | Servers: {len(client.guilds)} | Backgrounds: {bgs}")
    client.loop.create_task(cleanup_cooldowns())

# ================= ENABLE =================

@tree.command(name="enable", description="Bật bot")
async def enable(interaction: discord.Interaction):
    if str(interaction.user.id) not in BOT_OWNERS:
        return await interaction.response.send_message("❌ Chỉ admin chính mới dùng được.")

    guild_id = str(interaction.guild_id)

    if guild_id not in permissions:
        permissions[guild_id] = {"enabled": True, "allowedUsers": []}
    else:
        permissions[guild_id]["enabled"] = True

    save_permissions()
    log_action({"action": "enable", "guildId": guild_id, "by": str(interaction.user.id)})
    await interaction.response.send_message("✅ Bot đã bật ở server này.")

# ================= DISABLE =================

@tree.command(name="disable", description="Tắt bot")
async def disable(interaction: discord.Interaction):
    if str(interaction.user.id) not in BOT_OWNERS:
        return await interaction.response.send_message("❌ Chỉ admin chính mới dùng được.")

    guild_id = str(interaction.guild_id)

    if guild_id not in permissions:
        permissions[guild_id] = {"enabled": False, "allowedUsers": []}
    else:
        permissions[guild_id]["enabled"] = False

    save_permissions()
    log_action({"action": "disable", "guildId": guild_id, "by": str(interaction.user.id)})
    await interaction.response.send_message("⛔ Bot đã tắt ở server này.")

# ================= GRANT =================

@tree.command(name="grant", description="Cấp quyền user")
@app_commands.describe(user="User")
async def grant(interaction: discord.Interaction, user: discord.User):
    if str(interaction.user.id) not in BOT_OWNERS:
        return await interaction.response.send_message("❌ Chỉ admin chính mới dùng được.")

    guild_id = str(interaction.guild_id)

    if guild_id not in permissions:
        permissions[guild_id] = {"enabled": False, "allowedUsers": []}

    if str(user.id) not in permissions[guild_id]["allowedUsers"]:
        permissions[guild_id]["allowedUsers"].append(str(user.id))

    save_permissions()
    log_action({"action": "grant", "guildId": guild_id, "by": str(interaction.user.id), "target": str(user.id)})
    await interaction.response.send_message(f"✅ Đã cấp quyền cho {user}")

# ================= REVOKE =================

@tree.command(name="revoke", description="Thu hồi quyền")
@app_commands.describe(user="User")
async def revoke(interaction: discord.Interaction, user: discord.User):
    if str(interaction.user.id) not in BOT_OWNERS:
        return await interaction.response.send_message("❌ Chỉ admin chính mới dùng được.")

    guild_id = str(interaction.guild_id)

    if guild_id in permissions:
        permissions[guild_id]["allowedUsers"] = [
            uid for uid in permissions[guild_id]["allowedUsers"]
            if uid != str(user.id)
        ]

    save_permissions()
    log_action({"action": "revoke", "guildId": guild_id, "by": str(interaction.user.id), "target": str(user.id)})
    await interaction.response.send_message(f"⛔ Đã thu hồi quyền của {user}")


# ================= PUBLIC =================

@tree.command(name="public", description="Cho phép tất cả mọi người trong server dùng bot")
async def public(interaction: discord.Interaction):
    if str(interaction.user.id) not in BOT_OWNERS:
        return await interaction.response.send_message("❌ Chỉ admin chính mới dùng được.")

    guild_id = str(interaction.guild_id)

    if guild_id not in permissions:
        permissions[guild_id] = {"enabled": False, "allowedUsers": [], "public": False}

    permissions[guild_id]["public"] = True
    save_permissions()
    log_action({"action": "public", "guildId": guild_id, "by": str(interaction.user.id)})
    logger.info(f"[PUBLIC] Guild: {interaction.guild} by {interaction.user}")
    await interaction.response.send_message("✅ Đã bật chế độ **công khai** — tất cả mọi người trong server đều dùng được bot.")

@tree.command(name="private", description="Chỉ user được cấp quyền mới dùng được bot")
async def private(interaction: discord.Interaction):
    if str(interaction.user.id) not in BOT_OWNERS:
        return await interaction.response.send_message("❌ Chỉ admin chính mới dùng được.")

    guild_id = str(interaction.guild_id)

    if guild_id not in permissions:
        permissions[guild_id] = {"enabled": False, "allowedUsers": [], "public": False}

    permissions[guild_id]["public"] = False
    save_permissions()
    log_action({"action": "private", "guildId": guild_id, "by": str(interaction.user.id)})
    logger.info(f"[PRIVATE] Guild: {interaction.guild} by {interaction.user}")
    await interaction.response.send_message("⛔ Đã tắt chế độ công khai — chỉ user được cấp quyền mới dùng được bot.")

# ================= LIST =================

@tree.command(name="list", description="Xem danh sách user được cấp quyền")
async def list_users(interaction: discord.Interaction):
    if str(interaction.user.id) not in BOT_OWNERS:
        return await interaction.response.send_message("❌ Chỉ admin chính mới dùng được.")

    guild_id = str(interaction.guild_id)

    if guild_id not in permissions or not permissions[guild_id]["allowedUsers"]:
        return await interaction.response.send_message("Không có user nào được cấp quyền.")

    text = "👥 Danh sách user được cấp quyền:\n\n"
    for uid in permissions[guild_id]["allowedUsers"]:
        text += f"<@{uid}>\n"

    await interaction.response.send_message(text)

# ================= UPT =================

@tree.command(name="upt", description="Trạng thái bot")
async def upt(interaction: discord.Interaction):
    if str(interaction.user.id) not in BOT_OWNERS:
        return await interaction.response.send_message("❌ Chỉ admin chính mới dùng được.")

    uptime_seconds = int(time.time() - bot_start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60

    latency = round(client.latency * 1000, 1)

    server_count = len(client.guilds)

    msg = "**[BOT STATUS]**\n"
    msg += f"|-- Uptime  : `{hours}h {minutes}m {seconds}s`\n"
    msg += f"|-- Speed   : `{latency}ms`\n"
    msg += f"|-- Servers : `{server_count} server`"

    await interaction.response.send_message(msg)

# ================= LIST_BG =================

@tree.command(name="list_bg", description="Xem danh sách background có sẵn")
async def list_bg(interaction: discord.Interaction):
    available = get_available_backgrounds()

    if not available:
        return await interaction.response.send_message("❌ Chưa có background nào.")

    await interaction.response.defer(ephemeral=True)

    msg = f"🖼️ **Danh sách background có sẵn ({len(available)}):**\n💡 Dùng: `/bxh bg: <tên background>`"
    await interaction.followup.send(msg, ephemeral=True)

    for bg in available:
        bg_path = f"backgrounds/{bg}.png"
        if os.path.exists(bg_path):
            await interaction.followup.send(
                content=f"`{bg}`",
                file=discord.File(bg_path, filename=f"{bg}.png"),
                ephemeral=True
            )

# ================= BXH =================

@tree.command(name="bxh", description="Bảng xếp hạng")
@app_commands.describe(
    accountid="id_game",
    start_time="Thời gian bắt đầu (ngày/tháng/năm giờ:phút)",
    end_time="Thời gian kết thúc (ngày/tháng/năm giờ:phút)",
    background="Tên background, dùng /list_bg để xem tất cả",
    custom_name="Tên custom hiển thị trên bảng",
    logo_custom="Ảnh logo hiển thị cho tất cả đội (không bắt buộc)",
    remove_match="Xóa trận theo số thứ tự, cách nhau bằng dấu phẩy (vd: 1,3)",
    team_names="Đặt tên đội theo ID (vd: 123456789012=Team A,987654321098=Team B)",
    add_logo="Nhập tên key_logo đã tạo (vd: custom1)",
    champion_rush="Ngưỡng điểm kích hoạt Champion Rush (vd: 50)"
)
async def bxh(interaction: discord.Interaction, accountid: str, start_time: str, end_time: str, background: str, custom_name: str = "", logo_custom: discord.Attachment = None, remove_match: str = "", team_names: str = "", add_logo: str = "", champion_rush: int = 0):

    guild_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)

    await interaction.response.defer()

    if guild_id not in permissions or not permissions[guild_id].get("enabled"):
        return await interaction.followup.send("❌ Bot chưa bật.")

    is_public = permissions[guild_id].get("public", False)
    if user_id not in BOT_OWNERS and not is_public and user_id not in permissions[guild_id]["allowedUsers"]:
        return await interaction.followup.send("❌ Bạn chưa được cấp quyền.")

    # Parse team_names: id bỏ 2 số cuối → tên đội
    id_to_name = {}
    if team_names:
        try:
            for part in team_names.split(","):
                part = part.strip()
                if "=" not in part:
                    raise ValueError(f"Sai format: `{part}`")
                raw_id, raw_name = part.split("=", 1)
                raw_id = raw_id.strip()
                team_name_custom = raw_name.strip()
                if not team_name_custom:
                    raise ValueError(f"Tên đội trống tại ID: `{raw_id}`")
                if len(raw_id) < 3:
                    raise ValueError(f"ID quá ngắn: `{raw_id}`")
                id_prefix = raw_id[:-2]
                id_to_name[id_prefix] = team_name_custom
        except ValueError as ve:
            return await interaction.followup.send(f"❌ team_names không hợp lệ. {ve}\nFormat đúng: `123456789012=Team A,987654321098=Team B`")

    # Load logo map nếu có add_logo
    logo_map = {}  # id_prefix → file path
    if add_logo:
        logo_dir = f"logos/{add_logo}"
        if not os.path.exists(logo_dir):
            return await interaction.followup.send(f"❌ Không tìm thấy bộ logo `{add_logo}`.")
        for fname in os.listdir(logo_dir):
            name_part = fname.rsplit(".", 1)[0]
            logo_map[name_part] = os.path.join(logo_dir, fname)

    key = guild_id + "_" + user_id
    now = time.time()

    if key in cooldowns and now < cooldowns[key]:
        remaining = int(cooldowns[key] - now)
        logger.info(f"[COOLDOWN] {interaction.user} còn {remaining}s")
        return await interaction.followup.send(f"⏳ Vui lòng chờ {remaining}s.")

    cooldowns[key] = now + 10

    try:
        fetch_start = time.time()
        start_ts = convert_to_timestamp(start_time)
        end_ts = convert_to_timestamp(end_time)

        logo_bytes = None
        async with aiohttp.ClientSession() as session:
            if logo_custom:
                async with session.get(logo_custom.url) as logo_response:
                    if logo_response.status == 200:
                        logo_bytes = await logo_response.read()

            async with session.post(
                "https://congdong.ff.garena.vn/league-score-api/player/find-match",
                json={"accountId": accountid, "startTime": start_ts, "endTime": end_ts},
                headers=headers
            ) as list_res:
                list_data = await list_res.json(content_type=None)

        matches = list_data.get("matches", [])

        if remove_match:
            try:
                xoa_indexes = set(int(x.strip()) for x in remove_match.split(","))
                matches = [m for i, m in enumerate(matches, 1) if i not in xoa_indexes]
            except:
                return await interaction.followup.send("❌ Tham số remove_match không hợp lệ. Ví dụ: `1,3`")

        team_map = {}
        match_details = []
        cr_winner = None  # Đội vô địch Champion Rush

        async with aiohttp.ClientSession() as session:
            for idx, match in enumerate(matches):
                async with session.post(
                    "https://congdong.ff.garena.vn/league-score-api/match",
                    json={"matchId": match["id"]},
                    headers=headers
                ) as detail_res:
                    detail_json = await detail_res.json(content_type=None)

                detail_data = detail_json.get("match", {})
                ranks = detail_data.get("ranks", [])

                booyah_team = "Không có"
                for team in ranks:
                    if team.get("booyah") == 1:
                        name = (team.get("teamName") or "").strip()
                        if not name:
                            acc_names = team.get("accountNames") or []
                            name = acc_names[0].strip() if acc_names else ""
                        booyah_team = name if name else "Unknown"
                        break

                match_details.append({
                    "index": idx + 1,
                    "id": match["id"],
                    "booyah": booyah_team,
                    "success": bool(ranks)
                })

                if not ranks:
                    continue

                for team in ranks:
                    score = team.get("score", 0)
                    kill = team.get("kill", 0)
                    booyah = 1 if team.get("booyah") == 1 else 0

                    team_name = team.get("teamName")
                    current_ids = team.get("playerAccountIds", [])

                    # Tìm custom name và logo theo ID (so sánh bỏ 2 số cuối)
                    custom_display = None
                    custom_logo_path = None
                    for cid in current_ids:
                        cid_prefix = str(cid)[:-2] if len(str(cid)) >= 3 else str(cid)
                        if custom_display is None and cid_prefix in id_to_name:
                            custom_display = id_to_name[cid_prefix]
                        if custom_logo_path is None and cid_prefix in logo_map:
                            custom_logo_path = logo_map[cid_prefix]

                    if team_name and team_name.strip() != "":
                        keyname = "NAME_" + team_name.strip()

                        if keyname not in team_map:
                            team_map[keyname] = {
                                "displayName": custom_display or team_name.strip(),
                                "accountIds": current_ids,
                                "totalScore": 0,
                                "totalKill": 0,
                                "totalBooyah": 0,
                                "logoPath": custom_logo_path
                            }
                        elif custom_display and not team_map[keyname].get("customized"):
                            team_map[keyname]["displayName"] = custom_display
                            team_map[keyname]["customized"] = True

                        team_map[keyname]["totalScore"] += score
                        team_map[keyname]["totalKill"] += kill
                        team_map[keyname]["totalBooyah"] += booyah

                        # Kiểm tra Champion Rush
                        if champion_rush > 0 and cr_winner is None and booyah == 1:
                            score_before = team_map[keyname]["totalScore"] - score
                            if score_before >= champion_rush:
                                cr_winner = keyname

                    else:
                        found_key = None

                        for keyname in team_map:
                            existing_ids = team_map[keyname].get("accountIds", [])
                            common = [i for i in existing_ids if i in current_ids]

                            if len(common) >= 2:
                                found_key = keyname
                                break

                        if found_key:
                            if custom_display and not team_map[found_key].get("customized"):
                                team_map[found_key]["displayName"] = custom_display
                                team_map[found_key]["customized"] = True
                            team_map[found_key]["totalScore"] += score
                            team_map[found_key]["totalKill"] += kill
                            team_map[found_key]["totalBooyah"] += booyah

                            # Kiểm tra Champion Rush
                            if champion_rush > 0 and cr_winner is None and booyah == 1:
                                score_before = team_map[found_key]["totalScore"] - score
                                if score_before >= champion_rush:
                                    cr_winner = found_key
                        else:
                            new_key = "IDS_" + "-".join(sorted(map(str, current_ids)))
                            account_names = team.get("accountNames") or []
                            fallback_name = account_names[0] if account_names else ""
                            team_map[new_key] = {
                                "displayName": custom_display or fallback_name,
                                "accountIds": current_ids,
                                "totalScore": score,
                                "totalKill": kill,
                                "totalBooyah": booyah,
                                "logoPath": custom_logo_path
                            }
                            if custom_display:
                                team_map[new_key]["customized"] = True

                            # Kiểm tra Champion Rush (đội mới tạo không thể đã đạt ngưỡng trước)

        leaderboard = sorted(
            team_map.values(),
            key=lambda x: x["totalScore"],
            reverse=True
        )

        # Champion Rush: đội đạt ngưỡng điểm TRƯỚC rồi Booyah trận tiếp → lên top 1
        if champion_rush > 0 and cr_winner and cr_winner in team_map:
            cr_team = team_map[cr_winner]
            leaderboard = [cr_team] + [t for t in leaderboard if t is not cr_team]

        if not leaderboard:
            return await interaction.followup.send("❌ Không tìm thấy dữ liệu.")

        elapsed = round(time.time() - fetch_start, 1)
        so_doi = len(leaderboard)
        logger.info(f"[BXH] {interaction.user} | bg={background} | matches={len(match_details)} | teams={so_doi} | time={elapsed}s")

        info = f"🔍 **Thông tin chung**\n"
        info += f"🎮 ID-Game: `{accountid}`\n"
        info += f"⏱️  Time: `{elapsed}s`\n"
        info += f"🕐 Start-time: `{start_time}`\n"
        info += f"🕐 End-time: `{end_time}`\n"
        info += f"👥 Team: `{so_doi} đội`\n\n"

        info += f"🔍 **Danh sách {len(match_details)} trận:**\n"
        for m in match_details:
            status = "✅ success" if m["success"] else "❌ Thất bại"
            info += f"📄 Number {m['index']}:\n"
            info += f"🆔 MatchID: `{m['id']}`\n"
            info += f"🚦 Status: {status}\n"
            info += f"🥇 Booyah: `{m['booyah']}`\n"
        info += "└─────────────────"

        image = render_image(background, leaderboard, start_time, custom_name, logo_bytes, logo_map if add_logo else {})

        await interaction.followup.send(
            content=info,
            file=discord.File(fp=image, filename="leaderboard.png")
        )

    except FileNotFoundError as e:
        logger.error(f"[BXH] {e}")
        await interaction.followup.send(str(e))
    except Exception as e:
        import traceback
        logger.error(f"[BXH] {traceback.format_exc()}")
        await interaction.followup.send(f"❌ Lỗi: `{type(e).__name__}: {e}`")

# ================= ADD_LOGO =================

@tree.command(name="add_logo", description="Thêm logo cho đội")
@app_commands.describe(
    key_logo="Tên key logo (vd: custom1)",
    logo_1="Logo đội 1", id_1="ID người chơi đội 1",
    logo_2="Logo đội 2", id_2="ID người chơi đội 2",
    logo_3="Logo đội 3", id_3="ID người chơi đội 3",
    logo_4="Logo đội 4", id_4="ID người chơi đội 4",
    logo_5="Logo đội 5", id_5="ID người chơi đội 5",
    logo_6="Logo đội 6", id_6="ID người chơi đội 6",
    logo_7="Logo đội 7", id_7="ID người chơi đội 7",
    logo_8="Logo đội 8", id_8="ID người chơi đội 8",
    logo_9="Logo đội 9", id_9="ID người chơi đội 9",
    logo_10="Logo đội 10", id_10="ID người chơi đội 10",
    logo_11="Logo đội 11", id_11="ID người chơi đội 11",
    logo_12="Logo đội 12", id_12="ID người chơi đội 12",
)
async def add_logo(
    interaction: discord.Interaction,
    key_logo: str,
    logo_1: discord.Attachment, id_1: str,
    logo_2: discord.Attachment = None, id_2: str = "",
    logo_3: discord.Attachment = None, id_3: str = "",
    logo_4: discord.Attachment = None, id_4: str = "",
    logo_5: discord.Attachment = None, id_5: str = "",
    logo_6: discord.Attachment = None, id_6: str = "",
    logo_7: discord.Attachment = None, id_7: str = "",
    logo_8: discord.Attachment = None, id_8: str = "",
    logo_9: discord.Attachment = None, id_9: str = "",
    logo_10: discord.Attachment = None, id_10: str = "",
    logo_11: discord.Attachment = None, id_11: str = "",
    logo_12: discord.Attachment = None, id_12: str = "",
):
    guild_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)

    if guild_id not in permissions or not permissions[guild_id].get("enabled"):
        return await interaction.response.send_message("❌ Bot chưa bật.")

    if user_id not in BOT_OWNERS and user_id not in permissions[guild_id]["allowedUsers"]:
        return await interaction.response.send_message("❌ Bạn chưa được cấp quyền.")

    await interaction.response.defer()

    logo_dir = f"logos/{key_logo}"
    os.makedirs(logo_dir, exist_ok=True)

    pairs = [
        (logo_1, id_1), (logo_2, id_2), (logo_3, id_3), (logo_4, id_4),
        (logo_5, id_5), (logo_6, id_6), (logo_7, id_7), (logo_8, id_8),
        (logo_9, id_9), (logo_10, id_10), (logo_11, id_11), (logo_12, id_12),
    ]

    saved = []
    errors = []

    def crop_circle(img_bytes):
        from PIL import Image, ImageDraw
        import io
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        size = min(img.size)
        img = img.crop(((img.width - size)//2, (img.height - size)//2,
                        (img.width + size)//2, (img.height + size)//2))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    async with aiohttp.ClientSession() as session:
        for logo_att, team_id in pairs:
            if not logo_att or not team_id.strip():
                continue
            team_id = team_id.strip()
            if len(team_id) < 3:
                errors.append(f"ID quá ngắn: `{team_id}`")
                continue
            id_prefix = team_id[:-2]
            file_path = f"{logo_dir}/{id_prefix}.png"
            async with session.get(logo_att.url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    data = crop_circle(data)
                    with open(file_path, "wb") as f:
                        f.write(data)
                    saved.append(f"`{team_id}`")
                else:
                    errors.append(f"Không tải được logo của ID `{team_id}`")

    msg = f"✅ Đã lưu **{len(saved)}** logo vào bộ `{key_logo}`."
    if errors:
        msg += f"\n❌ {len(errors)} logo lỗi không lưu được."

    await interaction.followup.send(msg)

# ================= REMOVE_LOGO =================

@tree.command(name="remove_logo", description="Xóa bộ logo")
@app_commands.describe(key_logo="Tên bộ logo cần xóa")
async def remove_logo(interaction: discord.Interaction, key_logo: str):
    guild_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)

    if guild_id not in permissions or not permissions[guild_id].get("enabled"):
        return await interaction.response.send_message("❌ Bot chưa bật.")

    if user_id not in BOT_OWNERS and user_id not in permissions[guild_id]["allowedUsers"]:
        return await interaction.response.send_message("❌ Bạn chưa được cấp quyền.")

    logo_dir = f"logos/{key_logo}"
    if not os.path.exists(logo_dir):
        return await interaction.response.send_message(f"❌ Không tìm thấy bộ logo `{key_logo}`.")

    import shutil
    shutil.rmtree(logo_dir)
    await interaction.response.send_message(f"✅ Đã xóa bộ logo `{key_logo}`.")

# ================= FAKE HTTP SERVER =================

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthHandler(BaseHTTPRequestHandler):
    def _respond(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def do_GET(self): self._respond()
    def do_HEAD(self): self._respond()
    def do_POST(self): self._respond()
    def do_OPTIONS(self): self._respond()

    def log_message(self, format, *args):
        pass  # Tắt log HTTP để không rác console

def run_http():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info(f"HTTP server chạy tại port {port}")
    server.serve_forever()

threading.Thread(target=run_http, daemon=True).start()

client.run(TOKEN)
