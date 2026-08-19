# Yahub - Bot Tính Điểm Free Fire

Bot Discord dùng để tự động tính bảng xếp hạng (BXH) các giải đấu Free Fire, lấy dữ liệu trực tiếp từ hệ thống tính điểm cộng đồng Garena FF (`congdong.ff.garena.vn`) và xuất ra ảnh bảng xếp hạng đẹp mắt kèm logo, tên đội tùy chỉnh.

## Tính năng

- **Tính bảng xếp hạng tự động** (`/bxh`): lấy danh sách trận đấu theo ID phòng và khoảng thời gian, tổng hợp điểm, kill, Booyah của từng đội và xuất ra ảnh leaderboard.
- **Nhiều background/renderer**: mỗi nền (`bg`, `bg1`, `bg2`, `bg3`, `ddh`...) có một renderer riêng trong thư mục `renderers/`, dễ dàng thêm mới.
- **Tùy chỉnh tên đội** theo ID người chơi (`team_names`).
- **Logo đội tùy chỉnh**: upload và lưu theo bộ logo (`/add_logo`, `/remove_logo`), tự động crop tròn.
- **Champion Rush**: tự động đẩy đội đạt ngưỡng điểm rồi thắng Booyah trận kế tiếp lên hạng 1.
- **Xóa trận không hợp lệ** khỏi kết quả tính điểm (`remove_match`).
- **Quản lý quyền theo server**: bật/tắt bot, cấp/thu hồi quyền, chế độ công khai hoặc riêng tư cho từng server (`/enable`, `/disable`, `/grant`, `/revoke`, `/public`, `/private`, `/list`).
- **Theo dõi trạng thái bot** (`/upt`) và xem danh sách background (`/list_bg`).
- Ghi log thao tác (`logs.json`) và cấu hình quyền theo server (`permissions.json`).
- Có sẵn HTTP health-check server (phục vụ deploy trên Render.com dạng worker luôn "sống").

## Yêu cầu

- Python 3.10+
- Thư viện: `discord.py`, `aiohttp`, `Pillow` (xem `requirements.txt`)

## Cài đặt

```bash
git clone <repo-url>
cd Yahub-bottinhdiem-main
pip install -r requirements.txt
```

## Cấu hình

Tạo file `.env` ở thư mục gốc với nội dung:

```env
TOKEN=your_discord_bot_token
CLIENT_ID=your_discord_client_id
BOT_OWNERS=discord_user_id_1,discord_user_id_2
COOKIE=cookie_dang_nhap_congdong.ff.garena.vn
```

| Biến | Mô tả |
|---|---|
| `TOKEN` | Token của Discord bot |
| `CLIENT_ID` | Client ID của ứng dụng Discord |
| `BOT_OWNERS` | Danh sách user ID (cách nhau bằng dấu phẩy) có toàn quyền quản trị bot |
| `COOKIE` | Cookie đăng nhập trang tính điểm cộng đồng Garena FF, dùng để gọi API lấy dữ liệu trận đấu |

> Nếu không có file `.env`, bot sẽ tự động dùng biến môi trường hệ thống (phù hợp khi deploy lên Render/Railway/VPS).

## Chạy bot

```bash
python yahub-ltt-v33.py
```

## Danh sách lệnh (Slash Commands)

### Quản trị (chỉ `BOT_OWNERS`)
| Lệnh | Mô tả |
|---|---|
| `/enable` | Bật bot ở server hiện tại |
| `/disable` | Tắt bot ở server hiện tại |
| `/grant <user>` | Cấp quyền dùng bot cho user |
| `/revoke <user>` | Thu hồi quyền của user |
| `/public` | Cho phép tất cả mọi người trong server dùng bot |
| `/private` | Chỉ user được cấp quyền mới dùng được bot |
| `/list` | Xem danh sách user được cấp quyền |
| `/upt` | Xem trạng thái/uptime của bot |

### Sử dụng chung
| Lệnh | Mô tả |
|---|---|
| `/list_bg` | Xem danh sách background có sẵn |
| `/bxh` | Tính và xuất ảnh bảng xếp hạng |
| `/add_logo` | Thêm bộ logo cho các đội (tối đa 12 đội/lệnh) |
| `/remove_logo` | Xóa một bộ logo đã tạo |

#### Chi tiết `/bxh`
| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `accountid` | ✅ | ID phòng/tài khoản dùng để tra trận đấu |
| `start_time` | ✅ | Thời gian bắt đầu, định dạng `ngày/tháng/năm giờ:phút` |
| `end_time` | ✅ | Thời gian kết thúc, cùng định dạng |
| `background` | ✅ | Tên background (xem bằng `/list_bg`) |
| `custom_name` | ❌ | Tên giải đấu hiển thị trên ảnh |
| `logo_custom` | ❌ | Ảnh logo chung cho tất cả các đội |
| `remove_match` | ❌ | Xóa trận theo số thứ tự, vd: `1,3` |
| `team_names` | ❌ | Đặt tên đội theo ID, vd: `123456789012=Team A,987654321098=Team B` |
| `add_logo` | ❌ | Tên bộ logo (đã tạo bằng `/add_logo`) để gắn logo riêng cho từng đội |
| `champion_rush` | ❌ | Ngưỡng điểm kích hoạt luật Champion Rush |

## Cấu trúc dự án

```
Yahub-bottinhdiem-main/
├── yahub-ltt-v33.py       # File chính chạy bot
├── requirements.txt       # Thư viện phụ thuộc
├── render.yaml             # Cấu hình deploy trên Render.com
├── permissions.json        # Lưu quyền/trạng thái bật-tắt theo server
├── logs.json                # Log các thao tác quản trị
├── Arial-Bold.ttf          # Font dùng để render ảnh
├── backgrounds/             # Ảnh nền cho bảng xếp hạng
│   ├── bg1.png / bg2.png / bg3.png ...
├── coords/                  # Tọa độ vẽ chữ/logo tương ứng từng background (JSON)
├── renderers/                # Module render ảnh cho từng background
│   ├── bg.py, bg1.py, bg2.py, bg3.py, ddh.py ...
└── logos/                    # Bộ logo do người dùng tải lên (tạo tự động khi dùng /add_logo)
```

## Deploy lên Render.com

Dự án có sẵn `render.yaml` để deploy dạng **worker**. Bot mở kèm một HTTP server nhỏ (health-check) ở cổng lấy từ biến môi trường `PORT` (mặc định `8080`) để tránh bị Render tự động tắt do không có cổng lắng nghe.

> Lưu ý: `render.yaml` hiện đang trỏ `startCommand` tới `yahub-ltt-v32.py` — cần cập nhật lại thành `yahub-ltt-v33.py` (tên file hiện tại) trước khi deploy.

## Lưu ý bảo mật

- **Không commit file `.env`** hoặc để lộ `TOKEN`/`COOKIE` lên repository công khai.
- `COOKIE` dùng để xác thực với hệ thống tính điểm Garena FF — cookie có thể hết hạn theo thời gian và cần cập nhật lại khi bot báo lỗi lấy dữ liệu.
