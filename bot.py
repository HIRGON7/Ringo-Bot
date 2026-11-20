import os
import sqlite3
import discord
from datetime import datetime, timezone, timedelta
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
from database import (
    initialize_database,
    create_reminder,
    start_reminder_timer,
    get_server_reminders,
    delete_reminder,
    cleanup_completed_reminders,
    reset_bump_reminders
)

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@tasks.loop(seconds=10)
async def check_reminders():
    connection = sqlite3.connect("reminders.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            reminder_id,
            guild_id,
            channel_id,
            message,
            next_reminder_at,
            interval_seconds,
            loop_enabled,
            reminder_type,
            name
        FROM reminders
        WHERE enabled = 1
          AND next_reminder_at IS NOT NULL
    """)

    reminders = cursor.fetchall()
    connection.close()

    now = datetime.now(timezone.utc)

    for (
        reminder_id,
        guild_id,
        channel_id,
        message,
        next_time,
        interval_seconds,
        loop_enabled,
        reminder_type,
        reminder_name
    ) in reminders:

        scheduled_time = datetime.fromisoformat(next_time)

        if now < scheduled_time:
            continue

        connection = sqlite3.connect("reminders.db")
        cursor = connection.cursor()

        cursor.execute("""
            SELECT next_reminder_at
            FROM reminders
            WHERE reminder_id = ?
              AND guild_id = ?
              AND enabled = 1
        """, (reminder_id, guild_id))

        current = cursor.fetchone()
        connection.close()

        if current is None or current[0] is None:
            continue

        if datetime.now(timezone.utc) < datetime.fromisoformat(current[0]):
            continue

        channel = bot.get_channel(channel_id)

        if channel is None:
            print(f"Channel {channel_id} not found.")
            continue

        try:
            if (
                reminder_type == "bump"
                and reminder_name == "DISBOARD Bump"
                and loop_enabled
                and interval_seconds == 7200
            ):
                embed = discord.Embed(
                    title="🔥 Reader's Delight | Bump Reminder",
                    description=(
                        "📚 **It's time to bump!**\n\n"
                        "Help our reading community grow by using "
                        "**`/bump`**!\n\n"
                        "✨ Every bump helps more readers discover us."
                    ),
                    color=discord.Color.from_rgb(139, 92, 246)
                )
                embed.set_image(url="attachment://bump_banner.png")
                embed.set_footer(text="📖 Reader's Delight • Happy Reading!")

                await channel.send(
                    content="<@&1563274133524185138>",
                    embed=embed,
                    file=discord.File("bump_banner.png"),
                    allowed_mentions=discord.AllowedMentions(
                        everyone=False,
                        roles=[discord.Object(id=1563274133524185138)],
                        users=False
                    )
                )
            else:
                embed = discord.Embed(
                    title=f"🔔 {reminder_name}",
                    description=message,
                    color=discord.Color.from_rgb(139, 92, 246)
                )
                embed.set_footer(text="📖 Reader's Delight • Reminder")
                await channel.send(embed=embed)

        except (discord.DiscordException, OSError) as error:
            print(f"Failed to send reminder {reminder_id}: {error}")
            continue

        connection = sqlite3.connect("reminders.db")
        cursor = connection.cursor()

        if (
            reminder_type == "bump"
            and reminder_name == "DISBOARD Bump"
            and loop_enabled
            and interval_seconds == 7200
        ):
            cursor.execute("""
                UPDATE reminders
                SET next_reminder_at = NULL
                WHERE reminder_id = ?
                  AND guild_id = ?
                  AND next_reminder_at = ?
            """, (reminder_id, guild_id, current[0]))

            print(
                f"DISBOARD reminder {reminder_id} sent. "
                "🔥 Bump alert delivered! Waiting for the next bump to recharge the timer... ⏳."
            )

        elif loop_enabled and interval_seconds and interval_seconds > 0:
            next_reminder = (
                datetime.now(timezone.utc)
                + timedelta(seconds=interval_seconds)
            )

            cursor.execute("""
                UPDATE reminders
                SET next_reminder_at = ?
                WHERE reminder_id = ?
                  AND guild_id = ?
                  AND next_reminder_at = ?
            """, (
                next_reminder.isoformat(),
                reminder_id,
                guild_id,
                current[0]
            ))

            print(
                f"Reminder {reminder_id} sent! "
                f"Next reminder: {next_reminder}"
            )

        else:
            cursor.execute("""
                DELETE FROM reminders
                WHERE reminder_id = ?
                  AND guild_id = ?
                  AND next_reminder_at = ?
            """, (reminder_id, guild_id, current[0]))

            print(
                f"One-time reminder {reminder_id} sent and deleted!"
            )

        connection.commit()
        connection.close()


@bot.event
async def on_ready():
    if not getattr(bot, "commands_synced", False):
        synced = await bot.tree.sync()
        bot.commands_synced = True
        print(f"Synced {len(synced)} slash commands.")

    if not check_reminders.is_running():
        check_reminders.start()

    print(f"Bot is online! Logged in as {bot.user}")


@bot.event
async def on_guild_join(guild):
    print(f"Joined server: {guild.name}")
    print(f"Server ID: {guild.id}")


DISBOARD_BOT_ID = 302050872383242240


@bot.event
async def on_message(message):
    if message.author.id == DISBOARD_BOT_ID and message.guild:
        print("DISBOARD message received!")
        print(f"Content: {message.content!r}")

        texts = [message.content]

        for embed in message.embeds:
            print(f"Embed title: {embed.title!r}")
            print(f"Embed description: {embed.description!r}")

            texts.append(embed.title or "")
            texts.append(embed.description or "")

            for field in embed.fields:
                texts.append(field.name or "")
                texts.append(field.value or "")

        combined_text = " ".join(texts).lower()

        success_phrases = (
            "bump done!",
            "bump successful",
            "bumped successfully",
            "successfully bumped"
        )

        if any(phrase in combined_text for phrase in success_phrases):
            updated = reset_bump_reminders(
                message.guild.id,
                message.channel.id
            )

            print(
                f"🔥 Bump confirmed! Countdown recharged — next reminder in 2 hours!. "
                f"Reset {updated} reminders."
            )

    await bot.process_commands(message)


@bot.tree.command(
    name="reminder-create",
    description="Create a new reminder for this server"
)
@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
@app_commands.choices(
    unit=[
        app_commands.Choice(name="Minutes", value="minutes"),
        app_commands.Choice(name="Hours", value="hours"),
        app_commands.Choice(name="Days", value="days")
    ]
)
async def reminder_create(
    interaction: discord.Interaction,
    name: str,
    channel: discord.TextChannel,
    message: str,
    duration: app_commands.Range[int, 1, 129600],
    unit: app_commands.Choice[str],
    loop: bool
):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "You need Manage Server permission to create reminders.",
            ephemeral=True
        )
        return

    unit_seconds = {
        "minutes": 60,
        "hours": 3600,
        "days": 86400
    }

    interval_seconds = duration * unit_seconds[unit.value]

    if interval_seconds > 90 * 24 * 60 * 60:
        await interaction.response.send_message(
            "The maximum reminder interval is 90 days.",
            ephemeral=True
        )
        return

    reminder_id = create_reminder(
        guild_id=interaction.guild.id,
        name=name,
        reminder_type="bump",
        channel_id=channel.id,
        role_id=None,
        message=message,
        interval_seconds=interval_seconds,
        loop_enabled=loop
    )

    if reminder_id is None:
        await interaction.response.send_message(
            "This server has reached its limit of 5 reminders.",
            ephemeral=True
        )
        return

    next_reminder = start_reminder_timer(reminder_id)

    if next_reminder is None:
        await interaction.response.send_message(
            "Reminder saved, but its timer could not be started.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"Reminder created successfully!\n"
        f"Name: {name}\n"
        f"Channel: {channel.mention}\n"
        f"Message: {message}\n"
        f"Interval: {duration} {unit.name}\n"
        f"Loop: {'Enabled' if loop else 'Disabled'}\n"
        f"Next reminder: <t:{int(next_reminder.timestamp())}:R>",
        ephemeral=True
    )


class DeleteReminderView(discord.ui.View):
    def __init__(self, guild_id, reminder_id, owner_id):
        super().__init__(timeout=60)
        self.guild_id = guild_id
        self.reminder_id = reminder_id
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Only the moderator who requested this deletion can confirm it.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="Delete Reminder",
        style=discord.ButtonStyle.danger,
        emoji="🗑️"
    )
    async def confirm_delete(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        deleted = delete_reminder(self.guild_id, self.reminder_id)

        for item in self.children:
            item.disabled = True

        if deleted:
            await interaction.response.edit_message(
                content="Reminder was deleted successfully.",
                view=self
            )
        else:
            await interaction.response.edit_message(
                content="Reminder not found. It may already have been deleted.",
                view=self
            )

        self.stop()

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary
    )
    async def cancel_delete(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            content="Deletion cancelled.",
            view=self
        )

        self.stop()


@bot.tree.command(
    name="reminder-list",
    description="Show all reminders in this server"
)
@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
async def reminder_list(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "You need Manage Server permission to view reminders.",
            ephemeral=True
        )
        return

    reminders = get_server_reminders(interaction.guild.id)

    if not reminders:
        await interaction.response.send_message(
            "This server has no reminders.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="Reminder Manager",
        description=f"Total reminders: {len(reminders)}/5",
        color=discord.Color.from_rgb(139, 90, 43)
    )

    for index, reminder in enumerate(reminders, start=1):
        (
            reminder_id,
            name,
            channel_id,
            interval_seconds,
            loop_enabled,
            enabled,
            next_reminder_at
        ) = reminder

        if next_reminder_at:
            next_time = datetime.fromisoformat(next_reminder_at)
            timestamp = int(next_time.timestamp())
            next_display = f"<t:{timestamp}:R>"
        elif name == "DISBOARD Bump" and loop_enabled:
            next_display = "⏳ Standing by! Awaiting the next successful bump to recharge the countdown... 🚀"
        else:
            next_display = "Not scheduled"

        if interval_seconds % 86400 == 0:
            interval_display = f"{interval_seconds // 86400} days"
        elif interval_seconds % 3600 == 0:
            interval_display = f"{interval_seconds // 3600} hours"
        else:
            interval_display = f"{interval_seconds // 60} minutes"

        embed.add_field(
            name=f"{index}. {name}",
            value=(
                f"Channel: <#{channel_id}>\n"
                f"Interval: {interval_display}\n"
                f"Loop: {'Yes' if loop_enabled else 'No'}\n"
                f"Next reminder: {next_display}"
            ),
            inline=False
        )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )
    
    
    
    

@bot.tree.command(
    name="reminder-delete",
    description="Delete a reminder from this server"
)
@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
async def reminder_delete(
    interaction: discord.Interaction,
    number: app_commands.Range[int, 1, 5]
):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "You need Manage Server permission to delete reminders.",
            ephemeral=True
        )
        return

    reminders = get_server_reminders(interaction.guild.id)

    if number > len(reminders):
        await interaction.response.send_message(
            f"Invalid number. This server has {len(reminders)} reminders.",
            ephemeral=True
        )
        return

    selected = reminders[number - 1]

    reminder_id = selected[0]
    reminder_name = selected[1]

    view = DeleteReminderView(
        guild_id=interaction.guild.id,
        reminder_id=reminder_id,
        owner_id=interaction.user.id
    )

    await interaction.response.send_message(
        f"Are you sure you want to delete reminder #{number}?\n"
        f"Name: {reminder_name}\n"
        f"This action cannot be undone.",
        view=view,
        ephemeral=True
    )


if not TOKEN:
    raise ValueError("DISCORD_TOKEN is missing from .env")

initialize_database()

deleted = cleanup_completed_reminders()
print(f"Cleaned up {deleted} completed reminders.")

bot.run(TOKEN)
