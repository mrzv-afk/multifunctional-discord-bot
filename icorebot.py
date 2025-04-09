import discord
import io
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import aiohttp
from urllib.parse import urlparse
import logging
from discord.ui import Button, View, Modal, TextInput, Select
import os

logging.basicConfig(level=logging.DEBUG)

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

bot = discord.Client(intents=intents)
bot.tree = app_commands.CommandTree(bot)

ROLE_ID = 1327818776393023691

activities = [
    discord.Activity(type=discord.ActivityType.watching, name="как грабят поезд на iCore"),
    discord.Activity(type=discord.ActivityType.playing, name="icore.online:22005"),
    discord.Activity(type=discord.ActivityType.streaming, name="разработку iCore", url="https://www.twitch.tv/enemy_btw"),
    discord.Activity(type=discord.ActivityType.listening, name="радио iCore.Online"),
]

activity_index = 0

@tasks.loop(seconds=10)
async def change_activity():
    global activity_indexcd
    await bot.change_presence(activity=activities[activity_index], status=discord.Status.online)
    activity_index = (activity_index + 1) % len(activities)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} успешно запущен!')
    if not change_activity.is_running():
        change_activity.start()

    # Регистрация команд
    await bot.tree.sync()  # Это нужно для синхронизации команд со слэш-меню Discord
    print("Команды синхронизированы!")

@bot.event
async def on_member_join(member):
    await asyncio.sleep(1)
    role = member.guild.get_role(ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
            print(f'Выдана роль {role.name} пользователю {member.name}')
        except discord.Forbidden:
            print("Ошибка: У бота недостаточно прав для выдачи роли.")
        except discord.HTTPException as e:
            print(f"Ошибка Discord API: {e}")
    else:
        print(f"Ошибка: Роль с ID {ROLE_ID} не найдена!")

@bot.tree.command(name="say", description="Отправляет сообщение в указанный канал от имени бота")
@app_commands.describe(channel="Канал для отправки", message="Текст сообщения", file_url="Ссылка на файл (если есть)")
async def say(interaction: discord.Interaction, channel: discord.TextChannel, message: str = None, file_url: str = None):
    """Отправляет сообщение в указанный канал от имени бота"""

    # Проверка прав пользователя
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ У вас недостаточно прав.", ephemeral=True)
        return

    files = []

    # Если указан file_url, проверим его валидность
    if file_url:
        # Проверка корректности URL
        parsed_url = urlparse(file_url)
        logging.debug(f"Проверка URL: {file_url} => {parsed_url}")
        if not parsed_url.scheme or not parsed_url.netloc:
            await interaction.response.send_message("❌ Неверный URL. Пожалуйста, предоставьте действительный URL.", ephemeral=True)
            return
        
        # Попытка скачать файл
        try:
            async with aiohttp.ClientSession() as session:
                logging.debug(f"Попытка скачать файл с URL: {file_url}")
                async with session.get(file_url) as response:
                    logging.debug(f"Ответ от сервера: {response.status}, заголовки: {response.headers}")

                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')
                        logging.debug(f"Тип контента: {content_type}")

                        # Проверяем, что файл является изображением или другим поддерживаемым форматом
                        if 'image' in content_type:
                            file_data = await response.read()
                            filename = file_url.split("/")[-1]  # Извлекаем имя файла из URL
                            files.append(discord.File(io.BytesIO(file_data), filename=filename))
                        else:
                            await interaction.response.send_message("❌ Только изображения или поддерживаемые файлы.", ephemeral=True)
                            return
                    else:
                        await interaction.response.send_message(f"❌ Ошибка при загрузке файла. Статус: {response.status}", ephemeral=True)
                        return
        except aiohttp.ClientError as e:
            logging.error(f"Ошибка при загрузке файла: {str(e)}")
            await interaction.response.send_message(f"❌ Ошибка при попытке загрузить файл: {str(e)}", ephemeral=True)
            return

    # Отправка сообщения с файлом (если есть)
    try:
        await channel.send(content=message, files=files)
        # Уведомление пользователя
        await interaction.response.send_message("✅ Сообщение отправлено!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ У бота нет прав на отправку сообщений в этот канал.", ephemeral=True)
    except discord.HTTPException as e:
        logging.error(f"Ошибка при отправке сообщения в канал: {str(e)}")
        await interaction.response.send_message(f"❌ Ошибка Discord API: {e}", ephemeral=True)

usernames = ["депрессед"]
user_ids = ["916752835603992636", "860818346952884224"]

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if any(username.lower() in message.content.lower() for username in usernames):
        await message.reply("Не мешайте ему, он сейчас может быть очень занят!")
        return

    for user_id in user_ids:
        if f"<@{user_id}>" in message.content or f"<@!{user_id}>" in message.content:
            await message.reply("Не мешайте ему, он сейчас может быть очень занят!")
            return

# Пример других команд
@bot.tree.command(name="ping", description="Пинг бота")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Понг! Задержка: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="userinfo", description="Получить информацию о пользователе")
async def userinfo(interaction: discord.Interaction, user: discord.User = None):
    user = user or interaction.user
    embed = discord.Embed(title=f"Информация о пользователе {user.name}", description=f"ID: {user.id}")
    embed.set_thumbnail(url=user.avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverinfo", description="Информация о сервере")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"Информация о сервере {guild.name}", description=f"ID: {guild.id}")
    embed.set_thumbnail(url=guild.icon.url)
    await interaction.response.send_message(embed=embed)

# Пример команды с параметром
@bot.tree.command(name="clear", description="Очистить сообщения на канале")
async def clear(interaction: discord.Interaction, amount: int):
    """Очистить сообщения в канале"""
    await interaction.response.defer()  # Ответить, что мы обрабатываем запрос
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Удалено {amount} сообщений.")

@bot.tree.command(name="help", description="Получить помощь по доступным командам")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="💡 Список команд бота",
        description="Используйте команды через слэш (/) для взаимодействия с ботом.",
        color=discord.Color.blue()
    )

    embed.add_field(name="/ping", value="Пинг бота.", inline=False)
    embed.add_field(name="/userinfo", value="Получить информацию о пользователе.", inline=False)
    embed.add_field(name="/serverinfo", value="Получить информацию о сервере.", inline=False)
    embed.add_field(name="/clear", value="Очистить сообщения на канале (параметр: количество).", inline=False)
    embed.add_field(name="/say", value="Отправить сообщение в указанный канал с файлом (опционально).", inline=False)
    
    embed.add_field(name="💬 Развлекательные команды", value="!coinflip, !dice, !8ball, !joke, !meme", inline=False)
    
    embed.set_footer(text="Для помощи пишите команду /help")
    await interaction.response.send_message(embed=embed)

# ID основного сервера
MAIN_GUILD_ID = 1261295487475126442  # Укажите ID основного сервера

# Список связанных серверов (guild.id)
linked_guilds = [
    1326678821356961832,
    1356395692826038282,
    1356397525443284992,
    1356776494101299360,
]

@bot.tree.command(name="giverole", description="Выдать или забрать роль у пользователя на всех серверах")
@app_commands.describe(
    user="Пользователь, которому выдаем/забираем роль",
    role_name="Название роли",
    action="Выдать (по умолчанию) или убрать роль ('remove')"
)
async def giverole(interaction: discord.Interaction, user: discord.Member, role_name: str, action: str = "give"):
    """Выдает или забирает роль у пользователя на всех серверах"""

    # Делаем defer, чтобы избежать таймаута (бот уведомляет, что думает)
    await interaction.response.defer(thinking=True)

    # Проверяем права
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.followup.send("❌ У вас недостаточно прав для управления ролями!", ephemeral=True)
        return

    success_servers = []
    failed_servers = []

    for guild in bot.guilds:
        role = discord.utils.get(guild.roles, name=role_name)

        if role and guild.get_member(user.id):
            try:
                member = guild.get_member(user.id)
                if action.lower() == "remove":
                    await member.remove_roles(role)
                    action_text = "забрана"
                else:
                    await member.add_roles(role)
                    action_text = "выдана"

                success_servers.append(guild.name)

            except discord.Forbidden:
                failed_servers.append(guild.name)

    # Формируем итоговый ответ
    if success_servers:
        success_msg = f"✅ Роль `{role_name}` {action_text} пользователю {user.mention} на серверах:\n" + ", ".join(success_servers)
    else:
        success_msg = "❌ Не удалось выдать роль ни на одном сервере."

    if failed_servers:
        fail_msg = f"⚠️ Бот не имеет прав управлять ролью на серверах:\n" + ", ".join(failed_servers)
    else:
        fail_msg = ""

    await interaction.followup.send(f"{success_msg}\n{fail_msg}", ephemeral=True)

import discord
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput

CATEGORY_NAME = "Заявки"
MODERATOR_ROLE_ID = 1356776494101299360
ROLE_ACCEPT_LOCAL = 1356776580709355721
ROLE_ACCEPT_OFFICIAL = 1327818770504486963
OFFICIAL_SERVER_ID = 1261295487475126442
NEWS_CHANNEL_ID = 1356776897236828211

# Модалка для отклонения
class RejectApplicationModal(Modal, title="Отклонение заявки"):
    reason = TextInput(label="Причина отклонения", style=discord.TextStyle.long)

    def __init__(self, user: discord.Member, channel: discord.TextChannel, moderator: discord.Member):
        super().__init__()
        self.user = user
        self.channel = channel
        self.moderator = moderator

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await self.user.send(
                f"Доброго времени суток, уважаемый {self.user.display_name}.\n"
                f"Ваше заявление было отклонено по причине: {self.reason.value}\n"
                f"Если у вас есть вопросы, напишите Администратору в личные сообщения {self.moderator.mention}.\n"
                f"Приятного времяпровождения!"
            )
        except discord.Forbidden:
            pass

        await interaction.response.send_message("✅ Заявка отклонена", ephemeral=True)
        try:
            await self.channel.delete()
        except discord.NotFound:
            pass

# View с кнопками принять / отклонить
class ModerationView(View):
    def __init__(self, user: discord.Member, channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.user = user
        self.channel = channel

    @discord.ui.button(label="✅ Принять", style=discord.ButtonStyle.green, custom_id="accept_app")
    async def accept(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)

        # Выдача локальной роли
        local_role = interaction.guild.get_role(ROLE_ACCEPT_LOCAL)
        if local_role:
            await self.user.add_roles(local_role)

        # Выдача роли на основном сервере
        official_guild = interaction.client.get_guild(OFFICIAL_SERVER_ID)
        if official_guild:
            official_member = official_guild.get_member(self.user.id)
            official_role = official_guild.get_role(ROLE_ACCEPT_OFFICIAL)
            if official_member and official_role:
                await official_member.add_roles(official_role)

        # Отправка сообщения в ЛС
        try:
            news_mention = f"<#{NEWS_CHANNEL_ID}>"
            await self.user.send(
                f"Доброго времени суток, уважаемый игрок {self.user.display_name}.\n\n"
                f"Ваше заявление на статус **медиа** было **одобрено**! 🎉\n"
                f"Пожалуйста, ознакомьтесь с каналом {news_mention} — в нём публикуются важные новости и обновления.\n\n"
                f"Добро пожаловать!"
            )
        except discord.Forbidden:
            pass

        await interaction.response.send_message("✅ Заявка принята!", ephemeral=True)

        try:
            await self.channel.delete()
        except discord.NotFound:
            pass

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.red, custom_id="reject_app")
    async def reject(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)

        await interaction.response.send_modal(RejectApplicationModal(self.user, self.channel, interaction.user))

# Кнопка "Подать заявку"
class ApplicationButton(Button):
    def __init__(self):
        super().__init__(label="Подать заявку", style=discord.ButtonStyle.blurple, custom_id="app_button")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        # Категория
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        if not category:
            return await interaction.response.send_message("❌ Категория для заявок не найдена!", ephemeral=True)

        # Канал уже есть?
        channel_name = f"заявка-{user.display_name.lower()}"
        if discord.utils.get(guild.channels, name=channel_name):
            return await interaction.response.send_message("❌ У вас уже есть активная заявка!", ephemeral=True)

        # Роль модератора
        mod_role = guild.get_role(MODERATOR_ROLE_ID)
        if not mod_role:
            return await interaction.response.send_message("❌ Роль модератора не найдена! Обратитесь к администратору.", ephemeral=True)

        try:
            # Создаём канал без прав, потом перезапишем
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                reason=f"Приватный канал заявки для {user}"
            )

            # Перезапись прав
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True),
                mod_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, read_message_history=True, manage_channels=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, manage_channels=True, read_message_history=True)
            }

            await channel.edit(overwrites=overwrites)

            # Инструкция
            instructions = (
                f"{user.mention}, для подачи заявки заполните следующую информацию:\n\n"
                "**1.** Ссылка на Twitch/YouTube/TikTok канал:\n"
                "**2.** Что предлагаете? (стримы или видео, или и то, и то):\n"
                "**3.** Сколько готовы производить стримов/роликов в неделю:\n"
                "**4.** Какова продолжительность стримов *для стримеров*:\n"
                "**5.** Среднее кол-во зрителей на стримах *для стримеров*:\n"
                "**6.** Статистику за последний месяц:\n"
                "**7.** Расскажите о себе:"
            )

            await channel.send(instructions, view=ModerationView(user, channel))
            await interaction.response.send_message(f"✅ Ваш приватный канал создан: {channel.mention}", ephemeral=True)

        except Exception as e:
            print(f"[Ошибка создания канала]: {e}")
            await interaction.response.send_message("❌ Не удалось создать канал заявки", ephemeral=True)

# View с кнопкой подачи
class ApplicationView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ApplicationButton())

# Команда для размещения кнопки
@bot.tree.command(name="заявка", description="Создать кнопку для подачи заявок")
@app_commands.default_permissions(manage_messages=True)
async def application_command(interaction: discord.Interaction, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    view = ApplicationView()
    await channel.send("Нажмите кнопку ниже чтобы подать заявку:", view=view)
    await interaction.response.send_message("✅ Кнопка заявки создана!", ephemeral=True)

# Проблемы по категориям
problems = {
    "Проблемы со входом": [
        "SocialClub на аккаунте не совпадает с вашим",
        "Защита аккаунта"
    ],
    "Проблемы в игре": [
        "Съезжает разрешение",
        "Исчез полностью худ",
        "Не работает микрофон в игре",
        "Низкий FPS"
    ],
    "Проблемы с запуском": [
        "Ошибка инициализации ERR_GFX_D3D_INIT",
        "Не запускается после обновления",
        "Проблемы с настройками графики"
    ]
}

# Ответы на конкретные проблемы
problem_responses = {
    "SocialClub на аккаунте не совпадает с вашим":
        "Обратитесь в нашу поддержку через сайт https://icore-5.online/support",

    "Защита аккаунта":
        "Обратитесь в нашу поддержку через сайт https://icore-5.online/support",

    "Съезжает разрешение":
        "Перейдите в настройки графики, установите разрешение, соответствующее вашему монитору. "
        "Проверьте полноэкранный режим и примените настройки.",

    "Исчез полностью худ":
        "**В сюжетном режиме:** выберите родное разрешение монитора, режим в окне без рамки, "
        "**формат автоматический**. Убедитесь, что в `F10 → Настройки HUD` включён.\n\n"
        "**Дополнительно:** используйте VPN, перезайдите в игру 2 раза (через F1), "
        "перезапустите ПК, очистите папки `client_resources`, `RAGEMP_v_config.xml`, "
        "удалите `multiplayer.dll`, `multiplayer_old.dll`, `updater.exe` и т.п. Проверьте "
        "антивирус и исключения.\n\n"
        "Полный гайд: https://forum.icore-5.online/",

    "Не работает микрофон в игре":
        "Убедитесь, что микрофон выбран в настройках Windows и RAGE MP.\n"
        "- Проверьте `F10 → Настройки голоса`\n"
        "- Запустите Discord или игру от имени администратора\n"
        "- Убедитесь, что драйвера микрофона актуальны\n"
        "- Проверьте, не отключён ли микрофон в настройках приватности Windows",

    "Низкий FPS":
        "Понизьте настройки графики:\n"
        "- Выключите тени, сглаживание, постобработку\n"
        "- Убедитесь, что нет перегрева процессора/видеокарты\n"
        "- Закройте фоновые процессы (особенно браузеры, Discord)\n"
        "- Обновите драйвера видеокарты\n"
        "- Используйте команду `/fpslimit` в F8-консоли, чтобы выставить ограничение"
}

# Картинки к проблемам
problem_images = {
    "Исчез полностью худ": "https://i.imgur.com/9HFJ6rJ.png"
}

# Класс для выбора категории
class CategorySelect(Select):
    def __init__(self):
        options = [discord.SelectOption(label=category, description=f"Выберите: {category}") for category in problems]
        super().__init__(
            placeholder="Выберите категорию проблемы",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="category_select"
        )

    async def callback(self, interaction: discord.Interaction):
        selected_category = self.values[0]
        view = ProblemSelectView(selected_category)
        await interaction.response.edit_message(
            content=f"🔍 Вы выбрали категорию: **{selected_category}**. Теперь выберите проблему ниже:",
            view=view
        )

# Класс для выбора проблемы
class ProblemSelect(Select):
    def __init__(self, category: str):
        options = [discord.SelectOption(label=problem) for problem in problems[category]]
        super().__init__(
            placeholder="Выберите вашу проблему",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="problem_select"
        )
        self.category = category

    async def callback(self, interaction: discord.Interaction):
        selected_problem = self.values[0]
        description = problem_responses.get(selected_problem, "К сожалению, информация по данной проблеме отсутствует.")
        image_url = problem_images.get(selected_problem)

        embed = discord.Embed(
            title=selected_problem,
            description=description,
            color=discord.Color.blue()
        )

        if image_url:
            embed.set_image(url=image_url)

        view = ProblemSelectView(self.category)
        await interaction.response.edit_message(
            content=None,
            embed=embed,
            view=view
        )

# Кнопка "Назад"
class BackButton(Button):
    def __init__(self, category: str):
        super().__init__(label="🔙 Назад", style=discord.ButtonStyle.secondary)
        self.category = category

    async def callback(self, interaction: discord.Interaction):
        view = CategorySelectView()
        await interaction.response.edit_message(
            content="🔁 Вы вернулись в главное меню. Пожалуйста, выберите категорию ниже:",
            embed=None,
            view=view
        )

# View для выбора категории
class CategorySelectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CategorySelect())

# View для выбора проблемы
class ProblemSelectView(View):
    def __init__(self, category: str):
        super().__init__(timeout=None)
        self.add_item(ProblemSelect(category))
        self.add_item(BackButton(category))

# Кнопка "Мне нужна помощь"
class SupportButton(Button):
    def __init__(self):
        super().__init__(label="🆘 Мне нужна помощь", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            content="❓ Выберите категорию проблемы ниже:",
            view=CategorySelectView(),
            ephemeral=True
        )

# View с кнопкой "Мне нужна помощь"
class SupportButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SupportButton())

# on_ready событие
@bot.event
async def on_ready():
    print(f"✅ Бот запущен как {bot.user}")
    channel = bot.get_channel(1359186881702793438)  # Замените ID на нужный
    if channel:
        await channel.send("Нажмите на кнопку ниже, чтобы получить помощь:", view=SupportButtonView())

if __name__ == "__main__":
    try:
        bot.run('DISCORD_TOKEN')  # Замените на реальный токен
    except discord.LoginFailure:
        print("Ошибка: Указан неверный токен бота.")