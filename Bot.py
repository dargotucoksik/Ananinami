import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# ------------------ TICKET KAPATMA DÜĞMESİ ------------------
class CloseButton(discord.ui.View):
    @discord.ui.button(label="❌ Ticket Kapat", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel

        if not channel.name.startswith("ticket-"):
            await interaction.response.send_message("Bu komut sadece ticket kanallarında çalışır.", ephemeral=True)
            return

        await interaction.response.send_message("Ticket kapatılıyor…", ephemeral=True)
        await channel.delete()


# ------------------ TICKET AÇMA BUTONU ------------------
class TicketButton(discord.ui.View):
    def __init__(self, log_channel):
        super().__init__(timeout=None)
        self.log_channel = log_channel

    @discord.ui.button(label="Ticket Aç", style=discord.ButtonStyle.green, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        user = interaction.user

        # Zaten açık ticket var mı?
        existing = discord.utils.get(guild.channels, name=f"ticket-{user.id}")
        if existing:
            await interaction.response.send_message("Zaten açık bir ticketın var.", ephemeral=True)
            return

        # Kanal izinleri
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Ticket kanalı oluştur
        channel = await guild.create_text_channel(
            name=f"ticket-{user.id}",
            overwrites=overwrites
        )

        # Ticket kanalına hoş geldin mesajı + kapatma düğmesi
        await channel.send(
            f"{user.mention}, destek ekibi sizinle ilgilenecek.",
            view=CloseButton()
        )

        # Kullanıcıya bilgi ver
        await interaction.response.send_message(
            f"Ticket başarıyla açıldı: {channel.mention}",
            ephemeral=True
        )

        # Yönetici DM’leri
        for member in guild.members:
            if member.guild_permissions.administrator:
                try:
                    await member.send(f"📩 Yeni ticket açıldı: {channel.mention} — Kullanıcı: {user}")
                except:
                    pass

        # Log kanalına yaz
        await self.log_channel.send(f"📁 **Yeni Ticket:** {channel.mention} — **Açan:** {user}")


# ------------------ TICKET PANEL KOMUTU ------------------
@bot.tree.command(name="ticket", description="Ticket paneli oluşturur (Yalnızca yöneticiler).")
@app_commands.describe(baslik="Ticket panelinde üstte gözükecek başlık")
async def ticket(interaction: discord.Interaction, baslik: str):

    # Sadece admin
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Bu komutu sadece yöneticiler kullanabilir.", ephemeral=True)
        return

    guild = interaction.guild

    # Ticket log kanalı var mı?
    log_channel = discord.utils.get(guild.channels, name="ticket-log")
    if not log_channel:
        log_channel = await guild.create_text_channel("ticket-log")

    # Ticket butonu
    view = TicketButton(log_channel)

    await interaction.response.send_message(
        f"🎫 **{baslik}**\nAşağıdaki butona basarak ticket açabilirsiniz:",
        view=view
    )


# ------------------ BOT HAZIR ------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot aktif: {bot.user}")


bot.run(input("bot tokeniniz: "))
