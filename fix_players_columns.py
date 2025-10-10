"""One-time script to add missing columns to players table"""
import os
os.environ['FLASK_ENV'] = 'production'

from app import create_app, db
from sqlalchemy import text

app = create_app('production')

with app.app_context():
    # Add missing columns
    with db.engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE players ADD COLUMN IF NOT EXISTS email_invitations BOOLEAN DEFAULT TRUE NOT NULL;
        """))
        conn.execute(text("""
            ALTER TABLE players ADD COLUMN IF NOT EXISTS email_reminders BOOLEAN DEFAULT TRUE NOT NULL;
        """))
        conn.execute(text("""
            ALTER TABLE players ADD COLUMN IF NOT EXISTS email_notifications BOOLEAN DEFAULT TRUE NOT NULL;
        """))
        conn.commit()
    print("✅ Columns added successfully!")