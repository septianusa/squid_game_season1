# ============================================
# Squid Game - Game 3 (Tug of War)
# 4 Rounds Animated (stacked) — Platform gap + bound fall
# Top-down view, gender by color (same shape)
# Modified: Use exact team order provided by user
# ============================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from io import StringIO
from matplotlib.patches import Rectangle

# ----------------------
# THEME
# ----------------------
BG   = "#121212"
PINK = "#FF4FA3"   # female color
MALE = "#B0BEC5"   # male color
TXT  = "#EAEAEA"
ROPE_COLOR = "#c7a76c"

# ----------------------
# ROUND MATCHUPS
# ----------------------
rounds_df = pd.DataFrame({
    "round":  [1, 2, 3, 4],
    "left":   ["Team 1", "Team 4", "Team 2", "Team 3"],
    "right":  ["Team 7", "Team 5", "Team 8", "Team 6"],
    "winner": ["Team 1", "Team 4", "Team 8", "Team 3"]
})

# ----------------------
# ROSTER (exact order as user provided)
# ----------------------
roster_data = """player_number,team_name,gender
245,Team 7,Male
120,Team 7,Male
37,Team 7,Female
408,Team 7,Female
27,Team 7,Male
273,Team 7,Male
58,Team 7,Male
243,Team 7,Male
327,Team 7,Male
241,Team 7,Female
194,Team 5,Male
63,Team 5,Male
19,Team 5,Male
314,Team 5,Male
156,Team 5,Male
184,Team 5,Male
315,Team 5,Male
396,Team 5,Male
410,Team 5,Male
447,Team 5,Female
55,Team 2,Male
105,Team 2,Male
132,Team 2,Male
231,Team 2,Female
110,Team 2,Male
374,Team 2,Male
365,Team 2,Female
59,Team 2,Female
204,Team 2,Male
364,Team 2,Female
109,Team 3,Male
60,Team 3,Male
279,Team 3,Male
226,Team 3,Male
404,Team 3,Female
146,Team 3,Male
330,Team 3,Female
403,Team 3,Male
234,Team 3,Male
88,Team 3,Male
101,Team 1,Male
111,Team 1,Male
278,Team 1,Male
303,Team 1,Male
40,Team 1,Male
83,Team 1,Male
122,Team 1,Male
357,Team 1,Male
32,Team 1,Male
360,Team 1,Male
456,Team 4,Male
218,Team 4,Male
67,Team 4,Female
199,Team 4,Male
1,Team 4,Male
240,Team 4,Female
212,Team 4,Female
244,Team 4,Male
196,Team 4,Male
276,Team 4,Male
236,Team 6,Male
92,Team 6,Male
86,Team 6,Male
225,Team 6,Male
230,Team 6,Female
183,Team 6,Male
201,Team 6,Male
417,Team 6,Male
308,Team 6,Female
312,Team 6,Male
17,Team 8,Male
322,Team 8,Male
96,Team 8,Male
453,Team 8,Female
21,Team 8,Male
413,Team 8,Male
43,Team 8,Male
28,Team 8,Male
130,Team 8,Male
229,Team 8,Male
"""
roster_df = pd.read_csv(StringIO(roster_data))
roster_df["player_number"] = roster_df["player_number"].astype(int)

# preserve the given order within each team
team_to_players = {
    t: df.reset_index(drop=True)
    for t, df in roster_df.groupby("team_name", sort=False)
}

# ----------------------
# ANIMATION PARAMS
# ----------------------
FPS = 3  
FRAMES_LINEUP, FRAMES_PULL, FRAMES_DROP = 12, 30, 22
TOTAL_FRAMES = FRAMES_LINEUP + FRAMES_PULL + FRAMES_DROP

LEFT_ANCHOR_X, RIGHT_ANCHOR_X, CENTER_X, ROPE_Y = 0.16, 0.84, 0.50, 0.50
PLAT_Y0, PLAT_Y1, GAP_W = 0.36, 0.64, 0.14
PLAT_L_X0, PLAT_L_X1 = 0.06, CENTER_X - GAP_W/2
PLAT_R_X0, PLAT_R_X1 = CENTER_X + GAP_W/2, 0.94

ROPE_PULL_SHIFT_MAX, WINNER_RETREAT_MAX, LOSER_RESIST, DROP_FALL_Y = 0.04, 0.04, 0.015, 0.40

def alt_offsets(n=10, amp=0.06, jitter=0.01):
    offs, sign = [], 1
    for _ in range(n):
        offs.append(sign * (amp + np.random.uniform(-jitter, jitter)))
        sign *= -1
    return np.array(offs)

def side_x_positions(side="left", n=10, jitter=0.008):
    if side == "left":
        xs = np.linspace(LEFT_ANCHOR_X, CENTER_X - GAP_W/2 - 0.02, n)
    else:
        xs = np.linspace(RIGHT_ANCHOR_X, CENTER_X + GAP_W/2 + 0.02, n)[::-1]
    xs += np.random.uniform(-jitter, jitter, n)
    return xs

# ----------------------
# FIGURE
# ----------------------
fig = plt.figure(figsize=(8, 6.7), facecolor=BG)
fig.text(0.5, 0.965, "Game 3: Tug of War — 4 Rounds (Top-Down, Gap & Fall)",
         color=PINK, ha="center", va="center", fontsize=14, fontweight="bold")
fig.text(0.5, 0.025, "Gender by color (Female = pink, Male = steel-gray)",
         color=TXT, ha="center", va="center", fontsize=9)

row_h = 1.0 / (len(rounds_df) + 0.4)
round_art = []

for _, match in rounds_df.iterrows():
    r = int(match["round"])
    left_team, right_team, winner = match["left"], match["right"], match["winner"]
    loser = right_team if winner == left_team else left_team

    top, bottom = 0.90 - (r-1)*row_h, 0.90 - (r-1)*row_h - (row_h*0.80)
    ax = fig.add_axes([0.07, bottom, 0.86, (top-bottom)], facecolor=BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xticks([]); ax.set_yticks([])

    ax.add_patch(Rectangle((PLAT_L_X0, PLAT_Y0), PLAT_L_X1 - PLAT_L_X0, PLAT_Y1 - PLAT_Y0,
                           facecolor="#1f1f1f", edgecolor="#444444", linewidth=1.0))
    ax.add_patch(Rectangle((PLAT_R_X0, PLAT_Y0), PLAT_R_X1 - PLAT_R_X0, PLAT_Y1 - PLAT_Y0,
                           facecolor="#1f1f1f", edgecolor="#444444", linewidth=1.0))

    rope_line = ax.plot([LEFT_ANCHOR_X, RIGHT_ANCHOR_X], [ROPE_Y, ROPE_Y],
                        color=ROPE_COLOR, lw=6, solid_capstyle="round")[0]

    ax.text(0.02, ROPE_Y + 0.07, f"Round {r}", color=TXT, fontsize=10, va="bottom")
    ax.text(0.12, ROPE_Y + 0.18, left_team,  ha="center", color=TXT, fontsize=11, weight="bold")
    ax.text(0.88, ROPE_Y + 0.18, right_team, ha="center", color=TXT, fontsize=11, weight="bold")
    ax.text(0.12 if winner==left_team else 0.88, ROPE_Y + 0.24, "WINNER",
            ha="center", color=PINK, fontsize=9, weight="bold")

    pull_dir = -1 if winner == left_team else +1

    left_df, right_df = team_to_players[left_team], team_to_players[right_team]
    lx, ly = side_x_positions("left", 10), np.full(10, ROPE_Y) + alt_offsets(10)
    rx, ry = side_x_positions("right", 10), np.full(10, ROPE_Y) + alt_offsets(10)

    left_pts, right_pts, left_txt, right_txt = [], [], [], []
    for i in range(10):
        g = str(left_df.loc[i,"gender"])
        color = PINK if g=="Female" else MALE
        p=ax.scatter(lx[i], ly[i], s=90, marker="o", c=color, edgecolor="white", lw=0.5, zorder=3)
        t=ax.text(lx[i], ly[i]+0.022, str(left_df.loc[i,"player_number"]).zfill(3),
                  ha="center", fontsize=9, color=TXT)
        left_pts.append(p); left_txt.append(t)

        g = str(right_df.loc[i,"gender"])
        color = PINK if g=="Female" else MALE
        p=ax.scatter(rx[i], ry[i], s=90, marker="o", c=color, edgecolor="white", lw=0.5, zorder=3)
        t=ax.text(rx[i], ry[i]+0.022, str(right_df.loc[i,"player_number"]).zfill(3),
                  ha="center", fontsize=9, color=TXT)
        right_pts.append(p); right_txt.append(t)

    round_art.append({"ax":ax,"rope_line":rope_line,"left_team":left_team,"right_team":right_team,
                      "winner":winner,"loser":loser,"pull_dir":pull_dir,
                      "L":{"x":lx,"y":ly,"pts":left_pts,"txt":left_txt},
                      "R":{"x":rx,"y":ry,"pts":right_pts,"txt":right_txt}})

# ----------------------
# UPDATE FUNCTION
# ----------------------
def update(frame):
    if frame < FRAMES_LINEUP: phase, pull_k, drop_k = "LINEUP",0,0
    elif frame < FRAMES_LINEUP+FRAMES_PULL: phase, pull_k, drop_k="PULL",(frame-FRAMES_LINEUP)/FRAMES_PULL,0
    else: phase, pull_k, drop_k="DROP",1,(frame-(FRAMES_LINEUP+FRAMES_PULL))/FRAMES_DROP; drop_k=np.clip(drop_k,0,1)

    for art in round_art:
        dx_rope = art["pull_dir"]*ROPE_PULL_SHIFT_MAX*pull_k
        art["rope_line"].set_xdata([LEFT_ANCHOR_X+dx_rope, RIGHT_ANCHOR_X+dx_rope])
        for side_key in ["L","R"]:
            arr, x, y = art[side_key], art[side_key]["x"].copy(), art[side_key]["y"].copy()
            is_left=(side_key=="L")
            is_winner=(is_left and art["winner"]==art["left_team"]) or ((not is_left) and art["winner"]==art["right_team"])
            is_loser=(is_left and art["loser"]==art["left_team"]) or ((not is_left) and art["loser"]==art["right_team"])
            if phase in ("LINEUP","PULL"):
                x+=np.random.uniform(-0.002,0.002,len(x)); y+=np.random.uniform(-0.002,0.002,len(y))
                if is_winner: x+=((-WINNER_RETREAT_MAX) if is_left else WINNER_RETREAT_MAX)*pull_k
                else: x+=((+LOSER_RESIST) if is_left else -LOSER_RESIST)*pull_k
            if phase=="DROP" and is_loser:
                gap_target_x=CENTER_X-(GAP_W/4) if is_left else CENTER_X+(GAP_W/4)
                x=x+(gap_target_x-x)*(0.25+0.50*drop_k); y=y-DROP_FALL_Y*(0.25+0.75*drop_k)
                x+=np.random.uniform(-0.01,0.01,len(x))
            elif phase=="DROP" and is_winner:
                y=y+(ROPE_Y-y)*0.08
            art[side_key]["x"], art[side_key]["y"]=x,y
            for i,pt in enumerate(arr["pts"]): pt.set_offsets([x[i],y[i]])
            for i,txt in enumerate(arr["txt"]): txt.set_position((x[i],y[i]+0.022))
    return []

# ----------------------
# RENDER
# ----------------------
ani=animation.FuncAnimation(fig, update, frames=TOTAL_FRAMES, interval=1000/FPS, blit=False, repeat=False)
out_name="game3_rounds_gap_fall_ordered.gif"
ani.save(out_name, writer="pillow", fps=FPS)
print(f"Saved GIF: {out_name}")
