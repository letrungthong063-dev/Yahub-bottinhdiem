from PIL import Image, ImageDraw, ImageFont
import json
import os
import io
from datetime import datetime

FONT_PATHS = [
    "Rajdhani-Bold.ttf",
]

def get_font(size):
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()

def create_image(leaderboard, start_str="", name_str="", logo_bytes=None):
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

    font_main = get_font(coords["font_size"])
    font_time = get_font(coords["time_font_size"])
    font_name = get_font(coords.get("name_font_size", 70))

    time_color = coords.get("time_color", "white")
    name_color = coords.get("name_color", "white")

    LOGO_SIZE = coords.get("logo_size", 100)

    # Chuẩn bị logo
    logo_img = None
    if logo_bytes:
        try:
            logo_img = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
            logo_img = logo_img.resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
        except:
            logo_img = None

    # Vẽ thời gian
    if start_str:
        try:
            dt = datetime.strptime(start_str, "%d/%m/%Y %H:%M")
            time_text = dt.strftime("%H:%M %d/%m")
        except:
            time_text = start_str
        draw.text((coords["time_x"], coords["time_y"]), time_text, font=font_time, fill=time_color)

    # Vẽ tên host
    if name_str:
        draw.text((coords["name_x"], coords["name_y"]), name_str.upper(), font=font_name, fill=name_color)

    # Vẽ cột trái #1-#6
    for i, team in enumerate(leaderboard[:6]):
        y = coords["left_y"][i]

        if logo_img:
            logo_y = y - LOGO_SIZE // 2 + 30
            background.paste(logo_img, (coords["left_logo_x"], logo_y), logo_img)

        draw.text((coords["left_team_x"], y), str(team["displayName"]), font=font_main, fill="white")
        draw.text((coords["left_elims_x"], y), str(team["totalKill"]), font=font_main, fill="white")
        draw.text((coords["left_booyah_x"], y), str(team["totalBooyah"]), font=font_main, fill="white")
        draw.text((coords["left_total_x"], y), str(team["totalScore"]), font=font_main, fill="white")

    # Vẽ cột phải #7-#12
    for i, team in enumerate(leaderboard[6:12]):
        y = coords["right_y"][i]

        if logo_img:
            logo_y = y - LOGO_SIZE // 2 + 30
            background.paste(logo_img, (coords["right_logo_x"], logo_y), logo_img)

        draw.text((coords["right_team_x"], y), str(team["displayName"]), font=font_main, fill="white")
        draw.text((coords["right_elims_x"], y), str(team["totalKill"]), font=font_main, fill="white")
        draw.text((coords["right_booyah_x"], y), str(team["totalBooyah"]), font=font_main, fill="white")
        draw.text((coords["right_total_x"], y), str(team["totalScore"]), font=font_main, fill="white")

    buffer = io.BytesIO()
    background.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
