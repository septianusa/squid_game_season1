# ============================================
# Squid Game - Game 1 (Redlight, Greenlight)
# ============================================

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

# ------------------------
# Manual Data Input
# ------------------------
data = [
    {"round":1,"status":"Backfacing","time":5.00,"eliminated":0,"survived":456},
    {"round":2,"status":"Facing","time":4.90,"eliminated":1,"survived":455},      # Only Player 324 eliminated
    {"round":3,"status":"Backfacing","time":3.18,"eliminated":150,"survived":306},# Player 250 + mass panic
    {"round":4,"status":"Facing","time":3.00,"eliminated":220,"survived":236},
    {"round":5,"status":"Backfacing","time":2.60,"eliminated":220,"survived":236},
    {"round":6,"status":"Facing","time":2.30,"eliminated":235,"survived":221},
    {"round":7,"status":"Backfacing","time":1.90,"eliminated":235,"survived":221},
    {"round":8,"status":"Facing","time":1.50,"eliminated":245,"survived":211},
    {"round":9,"status":"Backfacing","time":1.10,"eliminated":245,"survived":211},
    {"round":10,"status":"Facing","time":0.70,"eliminated":252,"survived":204},
    {"round":11,"status":"Backfacing","time":0.40,"eliminated":252,"survived":204},
    {"round":12,"status":"Facing","time":0.00,"eliminated":255,"survived":201},
]
df = pd.DataFrame(data)

# ------------------------
# Field & Players
# ------------------------
total_players = 456
field_length = 30   # Y-axis units
field_width  = 40   # X-axis units
np.random.seed(42)

# Spread players across width; start at y=0
players_x = np.random.uniform(-field_width/2, field_width/2, total_players)
players_y = np.zeros(total_players)

# Colors / statuses
# cyan = alive (generic), lime = player 250, orange = player 324, red = eliminated
colors = ["cyan"] * total_players
players_x[324] = +1.0  # 324 on the right
players_x[250] = -1.0  # 250 on the left
colors[324] = "orange"
colors[250] = "lime"

# ------------------------
# Plot Setup (Squid Game nuance)
# ------------------------
fig, ax = plt.subplots(figsize=(10,6))
ax.set_facecolor("black")
ax.set_xlim(-field_width/2, field_width/2)
ax.set_ylim(-2, field_length+2)

# Title at bottom (no emoji -> no font warnings)
fig.subplots_adjust(bottom=0.22)
ax.set_title("Squid Game — Red Light, Green Light",
             fontsize=14, weight="bold", y=-0.15, color="#ff007f")

# Clean arena (no ticks/labels)
ax.set_xticks([]); ax.set_yticks([])

# Start/Finish lines in hot pink
ax.axhline(0, color="#ff007f", linewidth=2)
ax.text(-field_width/2+1, -1.5, "START", fontsize=12, color="#ff007f", weight="bold")
ax.axhline(field_length, color="#ff007f", linewidth=2)
ax.text(-field_width/2+1, field_length+0.5, "FINISH", fontsize=12, color="#ff007f", weight="bold")

# Field length text (center)
ax.text(0, field_length/2, f"{field_length} meters", fontsize=11, ha="center", va="center",
        color="white", alpha=0.6, style="italic")

# Scatter + status text
scat = ax.scatter(players_x, players_y, c=colors, s=12, edgecolor="white", linewidth=0.3)
status_text = ax.text(-field_width/2+1, field_length+1, "", fontsize=11, ha="left", color="white")

# Legend (no emoji)
legend_handles = [
    Patch(facecolor="cyan",   edgecolor="white", label="Alive"),
    Patch(facecolor="lime",   edgecolor="white", label="Player 250"),
    Patch(facecolor="orange", edgecolor="white", label="Player 324"),
    Patch(facecolor="red",    edgecolor="white", label="Eliminated"),
]
legend = ax.legend(handles=legend_handles, loc="lower center", ncol=4,
                   bbox_to_anchor=(0.5, -0.28), frameon=False)
for t in legend.get_texts():
    t.set_color("white")

round_idx = [0]

# ------------------------
# Animation Update
# ------------------------
def update(frame):
    idx = round_idx[0]
    if idx >= len(df):
        return scat,

    row = df.iloc[idx]
    status = row["status"]
    survived = row["survived"]

    if status == "Backfacing":
        if row["round"] == 1:
            # First backfacing: 324 & 250 sprint; others tiny shuffle
            players_y[324] = 8.0
            players_y[250] = 7.5
            for i, c in enumerate(colors):
                if c == "cyan":
                    players_y[i] += np.random.uniform(0.1, 0.3)
        else:
            # Later backfacings: every survivor advances at least 5m
            for i, c in enumerate(colors):
                if c in ["cyan", "lime", "orange"]:  # survivors
                    players_y[i] += np.random.uniform(5.0, 7.0)
                    if players_y[i] > field_length:
                        players_y[i] = field_length

    else:  # Facing
        if row["round"] == 2:
            # Only Player 324 eliminated at first facing
            colors[324] = "red"
        else:
            # Generic elimination to match target survivors for this row
            current_survivors = [i for i, c in enumerate(colors) if c in ["cyan", "lime", "orange"]]
            to_eliminate = len(current_survivors) - survived
            if to_eliminate > 0:
                eliminate_ids = np.random.choice(current_survivors, to_eliminate, replace=False)
                for eid in eliminate_ids:
                    colors[eid] = "red"

    # Special: Round 3 (mass panic) — eliminate Player 250 + place him near the group
    if row["round"] == 3:
        players_y[250] = np.random.uniform(2.0, 4.0)  # behind 324, near front of group
        colors[250] = "red"

    # Final frame: ensure survivors reach finish line
    if row["round"] == df["round"].max():
        for i, c in enumerate(colors):
            if c in ["cyan", "lime", "orange"]:
                players_y[i] = field_length

    # Update plot elements
    scat.set_offsets(np.c_[players_x, players_y])
    scat.set_facecolor(colors)
    status_text.set_text(
        f"Round {row['round']}  |  {status}  |  Time left: {row['time']:.2f} min   "
        f"Alive: {row['survived']}  |  Eliminated: {row['eliminated']}"
    )

    round_idx[0] += 1
    return scat, status_text

# ------------------------
# Animate & Save
# ------------------------
ani = animation.FuncAnimation(fig, update, frames=len(df), interval=1200, repeat=False)
ani.save("squidgame_redlight.gif", writer="pillow", fps=4)

print("Simulation complete. GIF saved as 'squidgame_redlight.gif'")

# (Optional) for Colab User, download:
# from google.colab import files
# files.download("squidgame_redlight.gif")
