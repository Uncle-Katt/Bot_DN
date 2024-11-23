import discord
import random
import asyncio
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

random_numbers_generated = None
choices = {}
betting_open = False
active_channel = None
auto_running = False  # Biến để kiểm soát chế độ tự động
channel_data = {} # Dictionary lưu thông tin riêng cho từng kênh

# Emoji
ROLL_EMOJI = "<a:roll_dice:1306546380377948220>"
LEFT_EMOJI = "<:ArrowLeft:1307929716652511232>"
HIDE_EMOJI = "<:hide:1307978218711547966>"
RIGHT_EMOJI = "<:ArrowRight:1307929708876398642>"
COIN_EMOJI = "<a:coinpink:1307966637344948315>"
GACH_EMOJI = "<:gach:1307970730075361291>"
CHECK_EMOJI = "<a:check:1307190907044368424>"
NOTI_EMOJI = "<a:noti:1307901434011979869>"
DOT_EMOJI = "<a:dot:1307903753738784882>"
VERTICAL_EMOJI = "<:vertical:1307932215639933008>"
VERIFY_EMOJI = "<a:verify:1307922482807701555>"
DICE_EMOJIS = {
    1: "<:dice_1:1306549741311496253>",
    2: "<:dice_2:1306549751386341406>",
    3: "<:dice_3:1306549763180724267>",
    4: "<:dice_4:1306549772835885056>",
    5: "<:dice_5:1306549780561924138>",
    6: "<:dice_6:1306549788380237906>"
}

@bot.event
async def on_ready():
    print(f'Bot đã đăng nhập với tên: {bot.user}')

# Lệnh bật chế độ tự động
@bot.command()
async def auto_on(ctx):
    global auto_running
    if auto_running:
        await ctx.send("Chế độ tự động đã được bật.")
        return
    auto_running = True
    await ctx.send("Chế độ tự động đã được bật.")
    await auto_run(ctx)

# Lệnh tắt chế độ tự động
@bot.command()
async def auto_off(ctx):
    global auto_running
    if not auto_running:
        await ctx.send("Chế độ tự động đã được tắt.")
        return
    auto_running = False
    await ctx.send("Chế độ tự động đã được tắt.")

# Hàm chạy tự động
async def auto_run(ctx):
    global auto_running
    while auto_running:
        await start_betting(ctx, wait_time=10)
        await asyncio.sleep(6)

@bot.command()
async def bet(ctx, *choices_input):
    global channel_data

    # Kiểm tra nếu vòng cược đã bắt đầu trong kênh này
    if ctx.channel.id not in channel_data or not channel_data[ctx.channel.id]["betting_open"]:
        await ctx.send("Vòng cược chưa mở hoặc đã kết thúc.")
        return

    # Chuyển chuỗi nhập vào thành danh sách lựa chọn
    choices_input = [choice.lower() for choice in choices_input]
    valid_choices_cl = ['chẵn', 'lẻ']
    valid_choices_tx = ['tài', 'xỉu']

    # Phân loại lựa chọn
    cl_choice = next((choice for choice in choices_input if choice in valid_choices_cl), None)
    tx_choice = next((choice for choice in choices_input if choice in valid_choices_tx), None)

    if not cl_choice and not tx_choice:
        await ctx.send("Vui lòng chọn ít nhất một trong các loại cược: 'chẵn', 'lẻ', 'tài', 'xỉu'.")
        return

    player = ctx.author

    if player not in channel_data[ctx.channel.id]["choices"]:
        # Khởi tạo lựa chọn cho người chơi
        channel_data[ctx.channel.id]["choices"][player] = {"cl": None, "tx": None}

    # Xử lý cược Chẵn/Lẻ
    if cl_choice:
        if channel_data[ctx.channel.id]["choices"][player]["cl"] is not None:
            await ctx.send(f"{player.mention}, bạn đã đặt cược vào '{channel_data[ctx.channel.id]['choices'][player]['cl']}'. Bạn không thể thay đổi cược Chẵn/Lẻ nữa.", delete_after=2.5)
        else:
            channel_data[ctx.channel.id]["choices"][player]["cl"] = cl_choice

    # Xử lý cược Tài/Xỉu
    if tx_choice:
        if channel_data[ctx.channel.id]["choices"][player]["tx"] is not None:
            await ctx.send(f"{player.mention}, bạn đã đặt cược vào '{channel_data[ctx.channel.id]['choices'][player]['tx']}'. Bạn không thể thay đổi cược Tài/Xỉu nữa.", delete_after=2.5)
        else:
            channel_data[ctx.channel.id]["choices"][player]["tx"] = tx_choice

    # Thêm reaction vào tin nhắn của người chơi
    await ctx.message.add_reaction(VERIFY_EMOJI)

    # Thông báo lại lựa chọn của người chơi
    response = f"{player.mention} đã đặt cược:"
    if cl_choice:
        response += f" **Chẵn/Lẻ**: {cl_choice.capitalize()}"
    if tx_choice:
        response += f" **Tài/Xỉu**: {tx_choice.capitalize()}"
    await ctx.send(response, delete_after=5)

@bot.command()
async def start_betting(ctx, wait_time: int = 30):
    global channel_data

    if wait_time < 10:
        wait_time = 10
    elif wait_time > 60:
        wait_time = 60

    # Kiểm tra nếu vòng cược đang diễn ra ở kênh này
    if ctx.channel.id in channel_data and channel_data[ctx.channel.id]["betting_open"]:
        await ctx.send("# 🚫 Vòng cược hiện tại đang diễn ra. Vui lòng chờ đến khi kết thúc để bắt đầu vòng mới.", delete_after=5)
        return

    # Khởi tạo thông tin cho kênh
    channel_data[ctx.channel.id] = {
        "random_numbers_generated": random.sample(range(1, 7), 3),
        "betting_open": True,
        "choices": {},
        "active_channel": ctx.channel.id
    }

    total = sum(channel_data[ctx.channel.id]["random_numbers_generated"])
    result_cl = "chẵn" if total % 2 == 0 else "lẻ"
    result_tx = "xỉu" if 3 <= total <= 10 else "tài"

    await ctx.send(f"# **{CHECK_EMOJI} Vòng cược đã bắt đầu! (!bet <chẵn/lẻ> hoặc !bet <tài/xỉu>).**")

    countdown_message = await ctx.send(f"# {NOTI_EMOJI}Còn {wait_time} giây...")
    for remaining_time in range(wait_time, 0, -1):
        await countdown_message.edit(content=f"# {NOTI_EMOJI} Còn {remaining_time} giây...")
        await asyncio.sleep(1)

    await countdown_message.delete()

    # Thông báo kết quả
    random_numbers_generated = channel_data[ctx.channel.id]["random_numbers_generated"]
    kq_message = await ctx.send(f"# {HIDE_EMOJI}{COIN_EMOJI} **KẾT QUẢ** {COIN_EMOJI}")
    roll_message = await ctx.send(f"{VERTICAL_EMOJI}{ROLL_EMOJI} {ROLL_EMOJI} {ROLL_EMOJI}{VERTICAL_EMOJI}")
    await asyncio.sleep(2)

    updated_content = [ROLL_EMOJI, ROLL_EMOJI, ROLL_EMOJI]
    for i in range(3):
        new_emoji = DICE_EMOJIS[random_numbers_generated[i]]
        updated_content[i] = new_emoji
        await roll_message.edit(content=f"{VERTICAL_EMOJI} {' '.join(updated_content)} {VERTICAL_EMOJI}")
        await asyncio.sleep(1)

    updated_content = [str(random_numbers_generated[0]), str(random_numbers_generated[1]), str(random_numbers_generated[2])]
    await kq_message.edit(content=f"# {HIDE_EMOJI} {COIN_EMOJI} {updated_content[0]}{GACH_EMOJI}{updated_content[1]}{GACH_EMOJI}{updated_content[2]} {COIN_EMOJI}")
    result_message = await ctx.send(f"# {RIGHT_EMOJI}{total}{DOT_EMOJI}{result_cl.upper()}{DOT_EMOJI}{result_tx.upper()}{LEFT_EMOJI}")

    # Xử lý người đoán đúng
    correct_cl = [player.mention for player, bets in channel_data[ctx.channel.id]["choices"].items() if bets["cl"] == result_cl]
    correct_tx = [player.mention for player, bets in channel_data[ctx.channel.id]["choices"].items() if bets["tx"] == result_tx]

    # Tạo embed hiển thị kết quả
    embed = discord.Embed(title="Kết quả vòng cược", color=0xffbfc0)
    embed.add_field(
        name="**Chẵn/Lẻ**",
        value="\n".join(correct_cl) if correct_cl else "Không có ai đoán đúng!",
        inline=True,
    )
    embed.add_field(
        name="**Tài/Xỉu**",
        value="\n".join(correct_tx) if correct_tx else "Không có ai đoán đúng!",
        inline=True,
    )
    await ctx.send(embed=embed)

    # Đặt lại trạng thái
    await asyncio.sleep(5)
    channel_data[ctx.channel.id]["random_numbers_generated"] = None
    channel_data[ctx.channel.id]["choices"].clear()
    channel_data[ctx.channel.id]["betting_open"] = False




#token của bot
bot.run('')    