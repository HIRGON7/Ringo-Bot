
from database import initialize_database, create_reminder
import sqlite3

initialize_database()

reminder_id = create_reminder(
    guild_id=12345,
    name="Test Bump",
    reminder_type="bump",
    channel_id=67890,
    role_id=None,
    message="Time to bump the server!",
    interval_seconds=7200
)

print("Created reminder ID:", reminder_id)

connection = sqlite3.connect("reminders.db")
cursor = connection.cursor()

cursor.execute(
    "SELECT * FROM reminders WHERE reminder_id = ?",
    (reminder_id,)
)

reminder = cursor.fetchone()

print("Saved reminder:", reminder)

connection.close()
