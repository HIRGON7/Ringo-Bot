import sqlite3
from datetime import datetime, timedelta, timezone



def initialize_database():
    connection = sqlite3.connect("reminders.db")
    cursor = connection.cursor()

   
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS server_settings (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER,
            role_id INTEGER,
            interval_seconds INTEGER DEFAULT 7200,
            enabled INTEGER DEFAULT 0,
            next_reminder_at TEXT
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            reminder_type TEXT NOT NULL
                CHECK(reminder_type IN ('bump', 'countdown')),
            channel_id INTEGER NOT NULL,
            role_id INTEGER,
            message TEXT NOT NULL,
            interval_seconds INTEGER,
            target_at TEXT,
            next_reminder_at TEXT,
            enabled INTEGER NOT NULL DEFAULT 1,
            loop_enabled INTEGER NOT NULL DEFAULT 0
        )
    """)

   
    cursor.execute("PRAGMA table_info(reminders)")
    columns = [column[1] for column in cursor.fetchall()]

   
    if "loop_enabled" not in columns:
        cursor.execute("""
            ALTER TABLE reminders
            ADD COLUMN loop_enabled INTEGER NOT NULL DEFAULT 0
        """)

    connection.commit()
    connection.close()



def save_server_settings(guild_id, channel_id, role_id):
    connection = sqlite3.connect("reminders.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO server_settings
            (guild_id, channel_id, role_id, enabled)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(guild_id) DO UPDATE SET
            channel_id = excluded.channel_id,
            role_id = excluded.role_id,
            enabled = 1
    """, (guild_id, channel_id, role_id))

    connection.commit()
    connection.close()




def schedule_reminder(guild_id):
    connection = sqlite3.connect("reminders.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT interval_seconds
        FROM server_settings
        WHERE guild_id = ? AND enabled = 1
        """,
        (guild_id,)
    )

    result = cursor.fetchone()

    if result is None:
        connection.close()
        return None

    interval_seconds = result[0]

    next_reminder = datetime.now(timezone.utc) + timedelta(
        seconds=interval_seconds
    )

    cursor.execute(
        """
        UPDATE server_settings
        SET next_reminder_at = ?
        WHERE guild_id = ?
        """,
        (next_reminder.isoformat(), guild_id)
    )

    connection.commit()
    connection.close()

    return next_reminder




def create_reminder(
    guild_id,
    name,
    reminder_type,
    channel_id,
    role_id,
    message,
    interval_seconds=None,
    target_at=None,
    loop_enabled=False
):
    connection = sqlite3.connect("reminders.db")
    cursor = connection.cursor()

    try:
        connection.execute("BEGIN IMMEDIATE")

        
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM reminders
            WHERE guild_id = ?
            """,
            (guild_id,)
        )

        reminder_count = cursor.fetchone()[0]

   
        if reminder_count >= 5:
            connection.rollback()
            return None

        
        cursor.execute("""
            INSERT INTO reminders (
                guild_id,
                name,
                reminder_type,
                channel_id,
                role_id,
                message,
                interval_seconds,
                target_at,
                loop_enabled
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            guild_id,
            name,
            reminder_type,
            channel_id,
            role_id,
            message,
            interval_seconds,
            target_at,
            int(loop_enabled)
        ))

        reminder_id = cursor.lastrowid

        connection.commit()

        return reminder_id

    finally:
        connection.close()




def start_reminder_timer(reminder_id):
    connection = sqlite3.connect("reminders.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT interval_seconds
        FROM reminders
        WHERE reminder_id = ? AND enabled = 1
        """,
        (reminder_id,)
    )

    result = cursor.fetchone()

    if result is None or result[0] is None:
        connection.close()
        return None

    interval_seconds = result[0]

    next_reminder = datetime.now(timezone.utc) + timedelta(
        seconds=interval_seconds
    )

    cursor.execute(
        """
        UPDATE reminders
        SET next_reminder_at = ?
        WHERE reminder_id = ?
        """,
        (next_reminder.isoformat(), reminder_id)
    )

    connection.commit()
    connection.close()

    return next_reminder


def delete_reminder(guild_id, reminder_id):
    connection = sqlite3.connect("reminders.db")
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM reminders
        WHERE guild_id = ? AND reminder_id = ?
    """, (guild_id, reminder_id))

    deleted = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return deleted





def get_server_reminders(guild_id):
    connection = sqlite3.connect("reminders.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            reminder_id,
            name,
            channel_id,
            interval_seconds,
            loop_enabled,
            enabled,
            next_reminder_at
        FROM reminders
        WHERE guild_id = ?
        ORDER BY reminder_id
    """, (guild_id,))

    reminders = cursor.fetchall()
    connection.close()

    return reminders




def cleanup_completed_reminders():
    connection = sqlite3.connect("reminders.db")
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM reminders
        WHERE enabled = 0
          AND loop_enabled = 0
    """)

    deleted_count = cursor.rowcount

    connection.commit()
    connection.close()

    return deleted_count




def reset_bump_reminders(guild_id, channel_id):
    connection = sqlite3.connect("reminders.db")
    cursor = connection.cursor()

    next_reminder = datetime.now(timezone.utc) + timedelta(hours=2)

    cursor.execute("""
        UPDATE reminders
        SET next_reminder_at = ?
        WHERE guild_id = ?
          AND channel_id = ?
          AND reminder_type = 'bump'
          AND name = 'DISBOARD Bump'
          AND loop_enabled = 1
          AND enabled = 1
          AND interval_seconds = 7200
    """, (
        next_reminder.isoformat(),
        guild_id,
        channel_id
    ))

    updated_count = cursor.rowcount

    connection.commit()
    connection.close()

    return updated_count


