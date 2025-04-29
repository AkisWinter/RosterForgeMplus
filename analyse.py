from libs.sql_handler import SQLHandler
from config import DATABASE_URL
import matplotlib.pyplot as plt
from datetime import datetime
from sqlalchemy import text

def plot_character_progression(char_id: str):
    db = SQLHandler(DATABASE_URL)
    db.create_tables()

    session = db.session
    snapshots = session.execute(
        text("""
        SELECT timestamp, equipped_item_level, average_item_level, mythic_plus_score, achievement_points
        FROM character_snapshots
        WHERE char_id = :char_id
        ORDER BY timestamp
        """),
        {"char_id": char_id}
    ).fetchall()

    if not snapshots:
        print(f"No snapshot data found for '{char_id}'")
        return

    timestamps = [row[0] for row in snapshots]
    equipped_ilvl = [row[1] for row in snapshots]
    average_ilvl = [row[2] for row in snapshots]
    mythic_scores = [row[3] for row in snapshots]
    achievement_pts = [row[4] for row in snapshots]

    fig, axs = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

    axs[0].plot(timestamps, equipped_ilvl, marker='o', label="Equipped iLvl")
    axs[0].plot(timestamps, average_ilvl, marker='x', linestyle='--', label="Average iLvl")
    axs[0].set_ylabel("Item Level")
    axs[0].legend()

    axs[1].plot(timestamps, mythic_scores, color='green', marker='s', label="Mythic+ Score")
    axs[1].set_ylabel("Mythic+ Score")
    axs[1].legend()

    axs[2].plot(timestamps, achievement_pts, color='purple', marker='^', label="Achievement Points")
    axs[2].set_ylabel("Achievements")
    axs[2].legend()
    axs[2].set_xlabel("Date")

    plt.suptitle(f"Character Progression: {char_id}")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    char_id_input = input("Enter character ID (e.g. Akisfury-Antonidas): ")
    plot_character_progression(char_id_input)