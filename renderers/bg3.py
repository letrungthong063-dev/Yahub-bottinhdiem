from PIL import Image, ImageDraw, ImageFont
import json
import os
import io
from datetime import datetime

FONT_PATHS = [
    "Arial-Bold.ttf",
]

def get_font(size):
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()

def create_image(leaderboard, start_str="", name_str="", logo_bytes=None, logo_map={}, match_details=None):
    bg_path = "backgrounds/bg3.png"
    coord_path = "coords/bg3.json"

    if not os.path.exists(bg_path):
        raise FileNotFoundError("Khong tim thay background: bg3")
    if not os.path.exists(coord_path):
        raise FileNotFoundError("Khong tim thay file toa do: coords/bg3.json")

    with open(coord_path, "r") as f:
        coords = json.load(f)

    background = Image.open(bg_path).convert("RGBA")
    draw = ImageDraw.Draw(background)

    font_main         = get_font(coords["font_size"])
    font_time         = get_font(coords["time_font_size"])
    font_name         = get_font(coords["name_font_size"])
    font_game_booyah  = get_font(coords["game_booyah_font_size"])

    LOGO_SIZE   = coords.get("logo_size", 90)
    LOGO_X      = coords.get("logo_x", 528)
    LOGO_OFFSET = coords.get("logo_offset_y", 30)
    text_color  = coords.get("text_color", "#000d34")
    name_color  = coords.get("name_color", "white")
    booyah_color = coords.get("game_booyah_color", "white")

    # Vẽ thời gian
    if start_str:
        try:
            dt = datetime.strptime(start_str, "%d/%m/%Y %H:%M")
            time_text = dt.strftime("%H:%M %d/%m")
        except:
            time_text = start_str
        draw.text((coords["time_x"], coords["time_y"]), time_text, font=font_time, fill="white")

    # Vẽ tên host
    if name_str:
        draw.text((coords["name_x"], coords["name_y"]), name_str.upper(), font=font_name, fill=name_color)

    # Chuẩn bị logo chung
    logo_img = None
    if logo_bytes:
        try:
            logo_img = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
            logo_img = logo_img.resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
        except:
            logo_img = None

    # Vẽ bảng xếp hạng (tối đa 12 đội)
    for i, team in enumerate(leaderboard[:12]):
        y = coords["start_y"] + i * coords["line_height"]

        # Logo riêng từ logoPath, fallback về logo_bytes chung
        team_logo = None
        logo_path = team.get("logoPath")
        if logo_path and os.path.exists(logo_path):
            try:
                team_logo = Image.open(logo_path).convert("RGBA")
                team_logo = team_logo.resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
            except:
                team_logo = logo_img
        else:
            team_logo = logo_img

        if team_logo:
            logo_y = y - LOGO_SIZE + LOGO_OFFSET
            background.paste(team_logo, (LOGO_X, logo_y), team_logo)

        draw.text((coords["team_x"],  y), str(team["displayName"]),  font=font_main, fill=text_color)
        draw.text((coords["elims_x"], y), str(team["totalKill"]),     font=font_main, fill=text_color)
        draw.text((coords["booyah_x"],y), str(team["totalBooyah"]),   font=font_main, fill=text_color)
        draw.text((coords["total_x"], y), str(team["totalScore"]),    font=font_main, fill=text_color)

    # Vẽ booyah từng trận (tối đa 4 trận đầu)
    if match_details:
        game_x  = coords["game_booyah_x"]
        game_ys = coords["game_booyah_y"]
        for i, match in enumerate(match_details[:4]):
            booyah_name = match.get("booyah", "")
            if booyah_name and i < len(game_ys):
                draw.text((game_x, game_ys[i]), str(booyah_name), font=font_game_booyah, fill=booyah_color)

    buffer = io.BytesIO()
    background.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
