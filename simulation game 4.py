# ============================================
# Squid Game - Game 4 (Marbles)
# ============================================
# ============================================
# Squid Game - Game 4 (Marbles) Simulation (FIXED)
# - Uses provided match outcomes
# - Animates one match at a time (marbles transfer)
# - Exports GIF + CSV logs
# ============================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from io import StringIO
import math
import random

# ----------------------
# THEME
# ----------------------
BG   = "#121212"
TXT  = "#EAEAEA"
ACC  = "#FF007F"   # accent
WIN  = "#41C37A"   # winner green
LOS  = "#D9534F"   # loser red
MARBLE = "#c7a76c" # marble color

plt.rcParams["figure.facecolor"] = BG
plt.rcParams["axes.facecolor"] = BG
plt.rcParams["savefig.facecolor"] = BG

# ----------------------
# Manual Data Input
# ----------------------
raw_csv = """Order Finished,Game Name,Winning Player No.,Winning Player Name,Losing Player No.,Losing Player Name,Sub-Game Played,Notes
0,Marbles,212,Han Mi-nyeo,Did not find a partner due to odd number of players,N/A,None,
1,Marbles,17,Do Jung-soo,413,,N/A,
2,Marbles,360,,89,,N/A,
3,Marbles,62,,130,,N/A,
4,Marbles,151,,68,,N/A,
5,Marbles,96,,229,,N/A,
6,Marbles,101,Jang Deok-su,278,,Odd or Even / Dig a Hole,
7,Marbles,407,,43,,N/A,
8,Marbles,453,,85,,N/A,
9,Marbles,21,,276,,N/A,
10,Marbles,244,,196,Hit the Marbles Out,Possibly involved throwing at a group of marbles
11,Marbles,308,,158,,N/A,
12,Marbles,69,,70,,N/A,
13,Marbles,218,Cho Sang-woo,199,Ali Abdul,Odd or Even,
14,Marbles,67,Kang Sae-byeok,240,Ji-yeong,Throw marble close to wall,
15,Marbles,322,Jung Min-tae,28,,N/A,
16,Marbles,456,Seong Gi-hun,1,Oh Il-nam,Odd or Even,
"""

df = pd.read_csv(StringIO(raw_csv))
df["Winning Player No."] = df["Winning Player No."].astype(str)
df["Losing Player No."]  = df["Losing Player No."].astype(str)

# Normalize BYE / odd player row
def is_bye_row(row):
    txt = str(row["Losing Player No."]).lower()
    return "did not find a partner" in txt

df["is_bye"] = df.apply(is_bye_row, axis=1)

# ----------------------
# SIMULATION PARAMETERS
# ----------------------
FPS = 1
FRAMES_INTRO   = 2   # show names & sub-game
FRAMES_PLAY    = 3   # marble transfers
FRAMES_RESOLVE = 1   # winner celebration / loser fade
TOTAL_PER_MATCH = FRAMES_INTRO + FRAMES_PLAY + FRAMES_RESOLVE

START_MARBLES = 10  # each player starts with 10

def make_transfer_schedule(winner_target=20, steps=16, style="generic", rng=None):
    if rng is None:
        rng = random.Random(0)
    remaining = winner_target - START_MARBLES  # amount to gain
    gains = []
    if remaining <= 0:
        return [0]*steps
    if style == "odd_even":
        for _ in range(steps-1):
            gains.append(rng.choice([1,2,3]))
        gains.append(max(1, remaining - sum(gains)))
    elif style == "throw_wall":
        for _ in range(steps-1):
            gains.append(rng.choice([0,2,2,4]))
        gains.append(max(1, remaining - sum(gains)))
    elif style == "hit_out":
        for _ in range(steps-1):
            gains.append(rng.choice([1,2,3,4]))
        gains.append(max(1, remaining - sum(gains)))
    else:
        for _ in range(steps-1):
            gains.append(rng.choice([1,1,2,2,3]))
        gains.append(max(1, remaining - sum(gains)))

    s = sum(gains)
    if s != remaining and s > 0:
        gains = [max(0, round(g * remaining / s)) for g in gains]
        delta = remaining - sum(gains)
        for i in range(abs(delta)):
            gains[i % len(gains)] += 1 if delta > 0 else -1
    return gains

def subgame_style(subgame_text):
    s = str(subgame_text).lower()
    if "odd or even" in s: return "odd_even"
    if "throw marble close to wall" in s: return "throw_wall"
    if "hit the marbles out" in s: return "hit_out"
    return "generic"

# Precompute schedules per match
rng = random.Random(42)
schedules = []
for _, row in df.sort_values("Order Finished").iterrows():
    if row["is_bye"]:
        schedules.append([0]*16)  # harmless placeholder
        continue
    style = subgame_style(row["Sub-Game Played"])
    gains = make_transfer_schedule(winner_target=20, steps=16, style=style, rng=rng)
    schedules.append(gains)

# ----------------------
# ANIMATION SETUP
# ----------------------
fig, ax = plt.subplots(figsize=(9,6))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

title = ax.text(0.5, 0.96, "Game 4: Marbles", ha="center", va="top", color=ACC, fontsize=18, weight="bold")
subtitle = ax.text(0.5, 0.91, "", ha="center", va="top", color=TXT, fontsize=12)

# Arena elements
L_TILE = (0.12, 0.35, 0.26, 0.30)  # x,y,w,h
R_TILE = (0.62, 0.35, 0.26, 0.30)
LANE   = (0.41, 0.30, 0.18, 0.40)

ltile = plt.Rectangle(L_TILE[:2], L_TILE[2], L_TILE[3], fc="#1f1f1f", ec="#444444", lw=1.2)
rtile = plt.Rectangle(R_TILE[:2], R_TILE[2], R_TILE[3], fc="#1f1f1f", ec="#444444", lw=1.2)
lane  = plt.Rectangle(LANE[:2],   LANE[2],   LANE[3],   fc="#101010", ec="#333333", lw=1.0)
ax.add_patch(ltile); ax.add_patch(rtile); ax.add_patch(lane)

# Labels & counters
left_name  = ax.text(L_TILE[0]+L_TILE[2]/2, L_TILE[1]+L_TILE[3]+0.06, "", ha="center", color=TXT, fontsize=12, weight="bold")
right_name = ax.text(R_TILE[0]+R_TILE[2]/2, R_TILE[1]+R_TILE[3]+0.06, "", ha="center", color=TXT, fontsize=12, weight="bold")
left_num   = ax.text(L_TILE[0]+L_TILE[2]/2, L_TILE[1]-0.03, "", ha="center", color=TXT, fontsize=11)
right_num  = ax.text(R_TILE[0]+R_TILE[2]/2, R_TILE[1]-0.03, "", ha="center", color=TXT, fontsize=11)

left_count  = ax.text(L_TILE[0]+L_TILE[2]/2, 0.50, "", ha="center", color=TXT, fontsize=22, weight="bold")
right_count = ax.text(R_TILE[0]+R_TILE[2]/2, 0.50, "", ha="center", color=TXT, fontsize=22, weight="bold")

result_text = ax.text(0.5, 0.10, "", ha="center", color=TXT, fontsize=13)

# moving marbles (use Line2D points; ALWAYS pass sequences to set_data)
MARBLE_N = 12
marbles = [ax.plot([], [], "o", ms=10, color=MARBLE, markeredgecolor="white", markeredgewidth=0.6, alpha=0.95)[0]
           for _ in range(MARBLE_N)]

# ----------------------
# LOGGING
# ----------------------
step_logs = []   # per-frame transfer log
match_logs = []  # final outcome

# ----------------------
# FRAME UPDATE
# ----------------------
matches = df.sort_values("Order Finished").reset_index(drop=True)

def interp(a, b, t): return a + (b-a)*t

def set_point(m, x, y, visible=True):
    """Helper to move/hide a Line2D point safely (expects sequences)."""
    if visible:
        m.set_data([x], [y])
        m.set_alpha(0.95)
    else:
        m.set_data([np.nan], [np.nan])
        m.set_alpha(0.0)

def update(global_frame):
    # determine which match we're on
    match_idx = min(global_frame // TOTAL_PER_MATCH, len(matches)-1)
    frame_in_match = global_frame % TOTAL_PER_MATCH
    row = matches.loc[match_idx]

    # Winner (left), Loser (right) visuals
    winner_id   = str(row["Winning Player No."])
    winner_name = "" if pd.isna(row.get("Winning Player Name", "")) else str(row.get("Winning Player Name", ""))
    loser_id    = None if row["is_bye"] else str(row["Losing Player No."])
    loser_name  = "" if row["is_bye"] else ("" if pd.isna(row.get("Losing Player Name","")) else str(row.get("Losing Player Name","")))
    subgame = str(row.get("Sub-Game Played",""))
    notes   = "" if pd.isna(row.get("Notes","")) else str(row.get("Notes",""))

    # Arena header
    if row["is_bye"]:
        subtitle.set_text(f"Order {row['Order Finished']} • BYE (odd player): auto-advance")
    else:
        subtitle.set_text(f"Order {row['Order Finished']} • Sub-game: {subgame if subgame!='N/A' else '—'}")

    # Labels
    left_label  = (winner_name + " " if winner_name else "") + f"#{winner_id}"
    right_label = "" if row["is_bye"] else ((loser_name + " " if loser_name else "") + f"#{loser_id}")
    left_name.set_text(left_label.strip())
    right_name.set_text(right_label.strip())
    left_num.set_text("Winner side")
    right_num.set_text("" if row["is_bye"] else "Loser side")

    # Counts
    if row["is_bye"]:
        w_cnt = START_MARBLES
        l_cnt = 0
    else:
        gains = schedules[match_idx]
        steps = len(gains)

        # map FRAMES_PLAY frames → 'steps' transfer steps
        if frame_in_match < FRAMES_INTRO:
            step_idx = 0
            prog_in_step = 0.0
        elif frame_in_match < FRAMES_INTRO + FRAMES_PLAY:
            t = (frame_in_match - FRAMES_INTRO) / FRAMES_PLAY  # 0..1
            fpos = t * steps
            step_idx = int(min(steps-1, math.floor(fpos)))
            prog_in_step = fpos - step_idx
        else:
            step_idx = steps-1
            prog_in_step = 1.0

        gain_cum_before = sum(gains[:step_idx])
        gain_this       = gains[step_idx] if steps>0 else 0
        gain_progress   = gain_cum_before + gain_this * prog_in_step

        w_cnt = START_MARBLES + int(round(gain_progress))
        l_cnt = START_MARBLES - int(round(gain_progress))
        w_cnt = max(0, min(20, w_cnt))
        l_cnt = max(0, min(20, l_cnt))

        if FRAMES_INTRO <= frame_in_match < FRAMES_INTRO + FRAMES_PLAY:
            step_logs.append({
                "order": int(row["Order Finished"]),
                "winner_id": winner_id,
                "loser_id": loser_id,
                "frame": int(global_frame),
                "step_index": int(step_idx),
                "winner_count": int(w_cnt),
                "loser_count": int(l_cnt),
                "subgame": subgame
            })

    left_count.set_text(str(w_cnt))
    right_count.set_text("" if row["is_bye"] else str(l_cnt))

    # Tile colors by phase
    if frame_in_match < FRAMES_INTRO:
        ltile.set_edgecolor("#555555"); rtile.set_edgecolor("#555555")
    elif frame_in_match < FRAMES_INTRO + FRAMES_PLAY:
        ltile.set_edgecolor(WIN); rtile.set_edgecolor(LOS if not row["is_bye"] else "#444444")
    else:
        ltile.set_edgecolor(WIN); rtile.set_edgecolor(LOS if not row["is_bye"] else "#444444")

    # Result banner
    if frame_in_match >= FRAMES_INTRO + FRAMES_PLAY:
        if row["is_bye"]:
            result_text.set_text(f"{left_label} advances by BYE")
            result_text.set_color(ACC)
        else:
            result_text.set_text(f"WIN: {left_label}   •   ELIMINATED: {right_label}")
            result_text.set_color(ACC)
            if frame_in_match == FRAMES_INTRO + FRAMES_PLAY:
                match_logs.append({
                    "order": int(row["Order Finished"]),
                    "winner_id": winner_id,
                    "winner_name": winner_name,
                    "loser_id": loser_id,
                    "loser_name": loser_name,
                    "subgame": subgame,
                    "notes": notes,
                    "winner_final_marbles": 20,
                    "loser_final_marbles": 0
                })
    else:
        result_text.set_text("")

    # Animate marbles
    # Reset (hide) all
    for m in marbles:
        set_point(m, 0, 0, visible=False)

    if row["is_bye"]:
        # idle swirl over left tile
        cx = L_TILE[0]+L_TILE[2]*0.5
        cy = L_TILE[1]+L_TILE[3]*0.5
        for i, m in enumerate(marbles):
            ang = (i/len(marbles))*2*np.pi + (frame_in_match/10)
            set_point(m, cx + 0.06*np.cos(ang), cy + 0.04*np.sin(ang), visible=True)
    else:
        if FRAMES_INTRO <= frame_in_match < FRAMES_INTRO + FRAMES_PLAY:
            t_local = (frame_in_match - FRAMES_INTRO) / FRAMES_PLAY  # 0..1
            sx = R_TILE[0] + R_TILE[2]*0.50
            sy = R_TILE[1] + R_TILE[3]*0.55
            tx = L_TILE[0] + L_TILE[2]*0.52
            ty = L_TILE[1] + L_TILE[3]*0.55

            for i, m in enumerate(marbles):
                start = (i / len(marbles)) * 0.8
                tt = np.clip((t_local - start) / 0.2, 0, 1)
                x = interp(sx, tx, tt) + np.random.uniform(-0.005, 0.005)
                y = interp(sy, ty, tt) + np.random.uniform(-0.005, 0.005)
                if tt > 0:
                    set_point(m, x, y, visible=True)
                else:
                    set_point(m, 0, 0, visible=False)

    return [
        left_name, right_name, left_num, right_num,
        left_count, right_count, result_text, ltile, rtile, lane, subtitle, title,
        *marbles
    ]

# ----------------------
# RENDER
# ----------------------
total_frames = TOTAL_PER_MATCH * len(df)
ani = animation.FuncAnimation(fig, update, frames=total_frames, interval=1000/FPS, blit=False, repeat=False)

out_gif = "game4_marbles.gif"
ani.save(out_gif, writer="pillow", fps=FPS)
print(f"Saved GIF: {out_gif}")

# ----------------------
# SAVE LOGS
# ----------------------
df_steps = pd.DataFrame(step_logs)
df_out   = pd.DataFrame(match_logs)

df_steps.to_csv("game4_marbles_per_frame_steps.csv", index=False)
df_out.to_csv("game4_marbles_outcomes.csv", index=False)
print("Saved CSVs: game4_marbles_per_frame_steps.csv, game4_marbles_outcomes.csv")
