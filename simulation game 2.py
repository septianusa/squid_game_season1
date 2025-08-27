# ============================================
# Squid Game - Game 2 (Sugar Honeycomb)
# ============================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random

# =========================
# THEME (Squid Game)
# =========================
BG   = "#121212"   # near-black background
PINK = "#FF007F"   # guard pink for accents
TXT  = "#EAEAEA"   # light text
GRID = "#333333"

# =========================
# FINAL COUNTS (your data)
# =========================
data = pd.DataFrame([
    {"shape":"Circle",   "failed":25, "survived":18},
    {"shape":"Star",     "failed":22, "survived":37},
    {"shape":"Triangle", "failed":18, "survived":32},
    {"shape":"Umbrella", "failed":14, "survived":20},
])
data["total"] = data["failed"] + data["survived"]

# Visual lineup order (left → right)
shape_order = ["Circle", "Triangle", "Star", "Umbrella"]

# Marker/color per shape
shape_style = {
    "Circle":   dict(color="tab:blue",   marker="o"),
    "Triangle": dict(color="tab:green",  marker="^"),
    "Star":     dict(color="tab:orange", marker="*"),
    "Umbrella": dict(color="tab:purple", marker="P"),
}

# =========================
# BUILD PLAYERS
# =========================
random.seed(42)
np.random.seed(42)

line_x_positions = {sh: i*11 + 7 for i, sh in enumerate(shape_order)}

players = []
for sh in shape_order:
    row = data[data["shape"]==sh].iloc[0]
    for i in range(row["failed"]):
        players.append({"shape": sh, "status": "fail_sched", "x": line_x_positions[sh]+np.random.uniform(-1,1), "y": 28 - i*0.25})
    for i in range(row["survived"]):
        players.append({"shape": sh, "status": "working",    "x": line_x_positions[sh]+np.random.uniform(-1,1), "y": 24 - i*0.25})

players = pd.DataFrame(players)
players["fail_mode"] = None  # "break" or "timeout" for those who will fail

# =========================
# TIMELINE & POSITIONS
# =========================
FRAMES_LINEUP   = 15
FRAMES_SCATTER  = 18
FRAMES_CARVE    = 28
FRAMES_TIMEOUT  = 6
FRAMES_EXIT     = 10
TOTAL_FRAMES = FRAMES_LINEUP + FRAMES_SCATTER + FRAMES_CARVE + FRAMES_TIMEOUT + FRAMES_EXIT

X_MAX = max(line_x_positions.values()) + 12
Y_MAX = 32

scatter_x_range = (5, X_MAX-5)
scatter_y_range = (7, 20)
players["tx"] = np.random.uniform(*scatter_x_range, size=len(players))
players["ty"] = np.random.uniform(*scatter_y_range, size=len(players))

DOOR_Y = Y_MAX - 1
door_pos = {sh: (line_x_positions[sh], DOOR_Y) for sh in shape_order}
players["dx"] = players["shape"].map(lambda sh: door_pos[sh][0])
players["dy"] = players["shape"].map(lambda sh: door_pos[sh][1])

# =========================
# FAILURE & COMPLETION SCHEDULING
# =========================
# Share of failures that should occur exactly at time-out (can't finish in time)
TIMEOUT_FAIL_FRACTION = 0.20  # 20% at time-out, 80% during carving by break

# Partition failed players into: break vs timeout failures
fail_pool = players.index[players["status"]=="fail_sched"].tolist()
random.shuffle(fail_pool)
n_timeout = int(round(len(fail_pool) * TIMEOUT_FAIL_FRACTION))
timeout_failers = fail_pool[:n_timeout]           # eliminated at time=0 (can't finish)
break_failers   = fail_pool[n_timeout:]           # eliminated during carving

# Mark modes
players.loc[timeout_failers, "fail_mode"] = "timeout"
players.loc[break_failers,   "fail_mode"] = "break"

# IMPORTANT: Show timeout failers as if they are "working" until time=0
players.loc[timeout_failers, "status"] = "working"

# Spread break failures across the carving frames
break_batches = np.array_split(np.array(break_failers), FRAMES_CARVE) if len(break_failers) else [[] for _ in range(FRAMES_CARVE)]

# All true survivors must finish before time-out.
# Workers eligible to finish during carving = everyone "working" EXCEPT timeout-failers
finish_candidates = players.index[(players["status"]=="working") & (players["fail_mode"].isna())].tolist()
random.shuffle(finish_candidates)
finish_batches = np.array_split(np.array(finish_candidates), FRAMES_CARVE) if len(finish_candidates) else [[] for _ in range(FRAMES_CARVE)]

# =========================
# LOGGING SETUP
# =========================
logs_overall = []
logs_by_shape = []
timeout_elim_records = []  # exact players eliminated at time-out

def phase_name(frame):
    if frame < FRAMES_LINEUP: return "Lineup"
    if frame < FRAMES_LINEUP + FRAMES_SCATTER: return "Scatter"
    if frame < FRAMES_LINEUP + FRAMES_SCATTER + FRAMES_CARVE: return "Carving"
    if frame < FRAMES_LINEUP + FRAMES_SCATTER + FRAMES_CARVE + FRAMES_TIMEOUT: return "Timeout"
    return "Exit"

def compute_timeleft(frame):
    if frame < FRAMES_LINEUP:
        return 600
    elif frame < FRAMES_LINEUP + FRAMES_SCATTER:
        f = frame - FRAMES_LINEUP
        return int(600 - (f / FRAMES_SCATTER) * 180)  # 600→420
    elif frame < FRAMES_LINEUP + FRAMES_SCATTER + FRAMES_CARVE:
        f = frame - (FRAMES_LINEUP + FRAMES_SCATTER)
        return max(0, int(420 - (f / FRAMES_CARVE) * 360))  # 420→60
    elif frame < FRAMES_LINEUP + FRAMES_SCATTER + FRAMES_CARVE + FRAMES_TIMEOUT:
        f = frame - (FRAMES_LINEUP + FRAMES_SCATTER + FRAMES_CARVE)
        return max(0, int(60 - (f+1) * (60/FRAMES_TIMEOUT)))
    else:
        return 0

def log_frame_snapshot(frame):
    tl = compute_timeleft(frame)
    ph = phase_name(frame)

    finished_total = int((players["status"] == "finished").sum())
    eliminated_total = int((players["status"] == "failed").sum())

    logs_overall.append({
        "frame": frame, "timeleft": tl, "phase": ph,
        "finished_total": finished_total, "eliminated_total": eliminated_total
    })

    for sh in shape_order:
        m = (players["shape"] == sh)
        fin_c = int((players.loc[m, "status"] == "finished").sum())
        fail_c = int((players.loc[m, "status"] == "failed").sum())
        logs_by_shape.append({
            "frame": frame, "timeleft": tl, "phase": ph, "shape": sh,
            "finished_cum": fin_c, "eliminated_cum": fail_c
        })

# =========================
# ANIMATION
# =========================
fig, ax = plt.subplots(figsize=(10,7))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
ax.set_xlim(0, X_MAX+12); ax.set_ylim(0, Y_MAX)
ax.set_xticks([]); ax.set_yticks([])

fig.subplots_adjust(bottom=0.16)
fig.text(0.5, 0.09, "Game 2: Sugar Honeycombs (Dalgona)",
         ha="center", va="center", color=PINK, fontsize=15, fontweight="bold")

subtitle = ax.text(0.5, 1.005, "", transform=ax.transAxes, ha="center", va="bottom", color=TXT, fontsize=11)
timer_text = ax.text(2, Y_MAX-1.8, "", color=TXT, fontsize=10)

ax.axhline(4, color=GRID, linestyle="--", linewidth=1)
ax.text(1, 4.4, "Arena", color="#AAAAAA", fontsize=9)

for sh, (dx, dy) in door_pos.items():
    ax.plot([dx-1.2, dx+1.2], [dy, dy], color=PINK, linewidth=3, solid_capstyle="round")
    ax.text(dx, dy+0.6, f"{sh} Exit", color=PINK, fontsize=8, ha="center")

scatters = {}
for sh in shape_order:
    st = shape_style[sh]
    scatters[sh] = ax.scatter([], [], s=46, marker=st["marker"], c=st["color"],
                              alpha=0.95, edgecolor="white", linewidth=0.3, label=sh)
leg = ax.legend(loc="upper right", facecolor="#1e1e1e", edgecolor="#444", labelcolor="white")
for t in leg.get_texts(): t.set_color("white")

def apply_offsets():
    for sh in shape_order:
        m = players["shape"]==sh
        scatters[sh].set_offsets(players.loc[m, ["x","y"]].values)

def move_step(ix, tx, ty, step=0.6, jitter=0.02):
    if len(ix) == 0: return
    idx = np.array(ix)
    x = players.loc[idx, "x"].values; y = players.loc[idx, "y"].values
    dx = tx - x; dy = ty - y
    dist = np.hypot(dx, dy)
    big = dist > step
    nx = np.zeros_like(dx); ny = np.zeros_like(dy)
    nx[big] = dx[big] / dist[big]; ny[big] = dy[big] / dist[big]
    x[big] += nx[big] * step; y[big] += ny[big] * step
    x[~big] = tx[~big]; y[~big] = ty[~big]
    x += np.random.uniform(-0.02,0.02,len(x)); y += np.random.uniform(-0.02,0.02,len(y))
    players.loc[idx, "x"] = x; players.loc[idx, "y"] = y

def move_towards(ix, tx, ty, rate=0.15, jitter=0.02):
    if len(ix) == 0: return
    idx = np.array(ix)
    x = players.loc[idx, "x"].values; y = players.loc[idx, "y"].values
    x += (tx - x) * rate + np.random.uniform(-jitter, jitter, len(x))
    y += (ty - y) * rate + np.random.uniform(-jitter, jitter, len(y))
    players.loc[idx, "x"] = x; players.loc[idx, "y"] = y

def update(frame):
    if frame < FRAMES_LINEUP:
        phase = "Line up by shape"; time_left = 600
        players["x"] += np.random.uniform(-0.04, 0.04, len(players))
        players["y"] += np.random.uniform(-0.04, 0.04, len(players))

    elif frame < FRAMES_LINEUP + FRAMES_SCATTER:
        phase = "Blending to tables (stepwise)"
        f = frame - FRAMES_LINEUP
        time_left = int(600 - (f / FRAMES_SCATTER) * 180)
        move_step(players.index, players["tx"].values, players["ty"].values, step=0.6, jitter=0.03)

    elif frame < FRAMES_LINEUP + FRAMES_SCATTER + FRAMES_CARVE:
        phase = "Carving (breaks & finishers to doors)"
        f = frame - (FRAMES_LINEUP + FRAMES_SCATTER)
        time_left = int(420 - (f / FRAMES_CARVE) * 360)

        # Break eliminations this frame
        for idx in break_batches[f]:
            players.loc[idx, "status"] = "failed"
            players.loc[idx, "y"] -= np.random.uniform(0.35, 0.8)

        # Some workers (true survivors) finish this frame
        for idx in finish_batches[f]:
            if players.loc[idx, "status"] == "working":
                players.loc[idx, "status"] = "finished"

        # Motion
        fin = players.index[players["status"]=="finished"]
        if len(fin): move_towards(fin, players.loc[fin,"dx"].values, players.loc[fin,"dy"].values, rate=0.15, jitter=0.02)
        still = players.index[(players["status"]!="finished") & (players["status"]!="failed")]
        if len(still):
            players.loc[still, "x"] += np.random.uniform(-0.05, 0.05, len(still))
            players.loc[still, "y"] += np.random.uniform(-0.05, 0.05, len(still))

    elif frame < FRAMES_LINEUP + FRAMES_SCATTER + FRAMES_CARVE + FRAMES_TIMEOUT:
        phase = "Time-out: can't finish eliminated"
        f = frame - (FRAMES_LINEUP + FRAMES_SCATTER + FRAMES_CARVE)
        time_left = max(0, int(60 - (f+1) * (60/FRAMES_TIMEOUT)))

        if f == 0:
            # Eliminate ONLY the designated timeout-failers now
            if len(timeout_failers):
                players.loc[timeout_failers, "status"] = "failed"
                players.loc[timeout_failers, "y"] -= np.random.uniform(0.25, 0.6, len(timeout_failers))
                # Log who they are
                for idx in timeout_failers:
                    timeout_elim_records.append({
                        "frame": frame,
                        "timeleft": time_left,
                        "player_index": int(idx),
                        "shape": players.loc[idx, "shape"]
                    })
        # Finished keep moving to doors
        fin = players.index[players["status"]=="finished"]
        if len(fin): move_towards(fin, players.loc[fin,"dx"].values, players.loc[fin,"dy"].values, rate=0.12, jitter=0.02)

    else:
        phase = "Finished exit"; time_left = 0
        fin = players.index[players["status"]=="finished"]
        if len(fin): move_towards(fin, players.loc[fin,"dx"].values, players.loc[fin,"dy"].values, rate=0.10, jitter=0.02)

    # Colors
    face = []
    for i in players.index:
        sh = players.loc[i, "shape"]; base = shape_style[sh]["color"]
        st = players.loc[i, "status"]
        face.append("#8B0000" if st=="failed" else base)

    for sh in shape_order:
        m = players["shape"]==sh
        scatters[sh].set_color(np.array(face)[m])
        scatters[sh].set_offsets(players.loc[m, ["x","y"]].values)

    # HUD
    finished = int((players["status"]=="finished").sum())
    failed   = int((players["status"]=="failed").sum())
    subtitle.set_text(f"Phase: {phase}   |   Finished (Survived): {finished}   Eliminated: {failed}")
    timer_text.set_text(f"Time left: {time_left} sec")

    log_frame_snapshot(frame)
    return list(scatters.values()) + [subtitle, timer_text]

ani = animation.FuncAnimation(fig, update, frames=TOTAL_FRAMES, interval=200, blit=False, repeat=False)

# Save GIF
out_name = "dalgona_step_blend_bottom_title.gif"
ani.save(out_name, writer="pillow", fps=5)
print(f"Simulation complete. GIF saved as '{out_name}'")

# ---- BUILD & SAVE CSVs ----
df_overall = pd.DataFrame(logs_overall)
df_by_shape_cum = pd.DataFrame(logs_by_shape).sort_values(["frame","shape"]).reset_index(drop=True)

# Per-step (diff) by shape — aligned & non-negative
df_by_shape_step = df_by_shape_cum.copy()
df_by_shape_step["finished_step"] = (
    df_by_shape_step.groupby("shape")["finished_cum"].diff().fillna(df_by_shape_step["finished_cum"]).clip(lower=0).astype(int)
)
df_by_shape_step["eliminated_step"] = (
    df_by_shape_step.groupby("shape")["eliminated_cum"].diff().fillna(df_by_shape_step["eliminated_cum"]).clip(lower=0).astype(int)
)

# Timeout eliminated players (exact list, will be used for vizualization)
df_timeout_players = pd.DataFrame(timeout_elim_records)
df_overall.to_csv("game2_dalgona_overall_by_frame.csv", index=False)
df_by_shape_cum.to_csv("game2_dalgona_per_shape_cum.csv", index=False)
df_by_shape_step.to_csv("game2_dalgona_per_shape_step.csv", index=False)
df_timeout_players.to_csv("game2_dalgona_timeout_players.csv", index=False)

print("CSV saved:",
      "game2_dalgona_overall_by_frame.csv,",
      "game2_dalgona_per_shape_cum.csv,",
      "game2_dalgona_per_shape_step.csv,",
      "game2_dalgona_timeout_players.csv")
