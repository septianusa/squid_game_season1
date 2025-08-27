# ============================================
# Squid Game - Game 4 (Glass Stepping Stone)
# ============================================


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle

# ---------- Theme ----------
BG   = "#121212"
TXT  = "#EAEAEA"
ACC  = "#FF007F"
SAFE = "#39d98a"
FAIL = "#e55353"
PANE = "#1f1f1f"
EDGE = "#444444"

plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG})

# ---------- Safe path ----------
safe_side = {
     1:'L',  2:'R',  3:'R',  4:'R',  5:'R',  6:'L',
     7:'R',  8:'R',  9:'L', 10:'R', 11:'R', 12:'R',
    13:'L', 14:'L', 15:'L', 16:'R', 17:'R', 18:'L'
}
N_STEPS = 18

# ---------- Turn order & outcomes ----------
turn_order = [
    (1,  96,  "Eliminated"),
    (2,  308, "Eliminated"),
    (3,  62,  "Eliminated"),
    (4,  21,  "Eliminated"),
    (5,  453, "Eliminated"),
    (6,  244, "Eliminated"),
    (7,  151, "Eliminated"),
    (8,  407, "Eliminated"),
    (9,  101, "Eliminated"),
    (10, 322, "Eliminated"),  # push-out (no glass break)
    (11, 212, "Eliminated"),
    (12, 360, "Eliminated"),  # fallback (no glass break)
    (13, 17,  "Eliminated"),
    (14, 218, "Survived Stage"),
    (15, 67,  "Survived Stage"),
    (16, 456, "Survived Stage"),
]

# ---------- Scripted broken panes ----------
broken_by_pid = {
    96:  (2,  'L'),
    308: (3,  'L'),
    62:  (7,  'L'),
    21:  (5,  'L'),   # forgetting the correct step
    453: (8,  'L'),
    151: (9,  'R'),   # 9 safe=L → wrong=R (taking over 244)
    244: (10, 'L'),   # pushed by 407
    407: (11, 'L'),
    101: (13, 'R'),   # hugged 212
    212: (13, 'R'),   # hugged by 101
    17:  (18, 'R'),   # pushed by 218
    # 322: push-out only
}

# ---------- Causes for overlay ----------
cause_by_pid = {
    21:  "forgetting the correct step.",
    151: "position taking over player 244.",
    244: "pushed by player 407.",
    101: "player 212 hugged by player 101.",
    212: "player 212 hugged by player 101.",
    17:  "pushed by player 218.",
    322: "pushed out of arena (no glass).",
    360: "eliminated (no glass break).",
}

# ---------- Geometry ----------
X0, X1 = 0.05, 0.95
Ymid   = 0.50
pane_gap_y = 0.06
pane_h     = 0.10
left_y  = Ymid + pane_gap_y
right_y = Ymid - pane_gap_y

col_w  = (X1 - X0) / (N_STEPS + 2)
col_x  = [X0 + col_w*(i+1) for i in range(N_STEPS)]
start_pos = (X0 + col_w*0.40, Ymid)
end_pos   = (X1 - col_w*0.40, Ymid)

def pane_center(step, side):
    sx = col_x[step-1]
    sy = left_y if side=='L' else right_y
    return sx, sy

# ---------- Board ----------
fig, ax = plt.subplots(figsize=(12,6))
ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
ax.text(0.5, 0.95, "Game 5: Glass Stepping Stones", ha="center", va="top",
        color=ACC, fontsize=16, weight="bold")
ax.text(0.5, 0.91, "The simulation has been simplified for clarity.",
        ha="center", va="top", color=TXT, fontsize=11)

# platforms
start_rect = Rectangle((X0, right_y-0.12), col_w*0.8, 0.24, fc="#2a2a2a", ec=EDGE, lw=1.2)
end_rect   = Rectangle((X1-col_w*0.8, right_y-0.12), col_w*0.8, 0.24, fc="#2a2a2a", ec=EDGE, lw=1.2)
ax.add_patch(start_rect); ax.add_patch(end_rect)
ax.text(X0+col_w*0.4, Ymid, "Start", color=TXT, ha="center", va="center", fontsize=10)
ax.text(X1-col_w*0.4, Ymid, "End",   color=TXT, ha="center", va="center", fontsize=10)

# panes
pane_patches = {}
for i, sx in enumerate(col_x, start=1):
    pL = Rectangle((sx-col_w*0.35, left_y - pane_h/2),  col_w*0.7, pane_h, fc=PANE, ec=EDGE, lw=1.0)
    pR = Rectangle((sx-col_w*0.35, right_y - pane_h/2), col_w*0.7, pane_h, fc=PANE, ec=EDGE, lw=1.0)
    ax.add_patch(pL); ax.add_patch(pR)
    pane_patches[(i,'L')] = pL
    pane_patches[(i,'R')] = pR
    ax.text(sx, Ymid+0.17, str(i), color="#9aa0a6", fontsize=9, ha="center", va="center")

# players
pids = [pid for _,pid,_ in turn_order]
dots, labels = {}, {}
for pid in pids:
    d, = ax.plot([], [], marker="o", ms=12, color="#B0BEC5",
                 markeredgecolor="white", markeredgewidth=0.8, zorder=5)
    t = ax.text(0,0,"", color=TXT, fontsize=12, weight="bold", ha="center")
    dots[pid] = d; labels[pid] = t

status_text = ax.text(0.02, 0.06, "", ha="left", color=TXT, fontsize=11)
cause_text  = ax.text(0.98, 0.06, "", ha="right", color=ACC, fontsize=11, style="italic")

# ---------- Timing (your request) ----------
FPS = 1
FRAMES_HOP_SYNC = 1
FRAMES_FALL     = 2
FRAMES_PAUSE    = 1
FRAMES_EXIT     = 1
FRAMES_PUSH     = 2

def lerp(a, b, t): return a + (b - a) * t

# ---------- State ----------
state = {}
for _, pid, _ in turn_order:
    state[pid] = dict(place=("start", 0), pos=start_pos, alive=True, finished=False, visible=True)

broken_panes = set()
revealed_safe_draw = {s: False for s in range(1, N_STEPS+1)}

# storyboard frames
frames = []
def snapshot(status_note="", cause_note=""):
    players_pos = {pid: (state[pid]["pos"][0], state[pid]["pos"][1], state[pid]["visible"]) for pid in pids}
    frames.append({
        "players": players_pos,
        "pane_safe": set([s for s,v in revealed_safe_draw.items() if v]),
        "pane_broken": set(broken_panes),
        "status": status_note,
        "cause": cause_note
    })

# ---------- Helpers ----------
def alive_queue():
    return [pid for (_, pid, _) in turn_order if state[pid]["alive"] and not state[pid]["finished"]]

def plan_followers_after_leader_arrival(leader_step, leader_pid):
    occupied = {leader_step}
    followers_on_pane = []
    followers_at_start = []

    for pid in alive_queue():
        if pid == leader_pid:
            continue
        loc, s = state[pid]["place"]
        if loc == "pane":
            occupied.add(s)
            followers_on_pane.append((s, pid))
        elif loc == "start":
            followers_at_start.append(pid)

    followers_on_pane.sort(reverse=True)
    planned = []

    for s, pid in followers_on_pane:
        target = s + 1
        if target <= leader_step - 1 and target not in occupied:
            start_xy = state[pid]["pos"]
            end_xy   = pane_center(target, safe_side[target])
            planned.append((pid, start_xy, end_xy, ("pane", target)))
            occupied.add(target)
            occupied.discard(s)
            revealed_safe_draw[target] = True

    if leader_step >= 2 and 1 not in occupied and followers_at_start:
        pid = followers_at_start[0]
        start_xy = state[pid]["pos"]
        end_xy   = pane_center(1, safe_side[1])
        planned.append((pid, start_xy, end_xy, ("pane", 1)))
        occupied.add(1)
        revealed_safe_draw[1] = True

    return planned

def hop_with_queue(pid, step, capture=True):
    leader_start = state[pid]["pos"]
    leader_end   = pane_center(step, safe_side[step])
    planned_followers = plan_followers_after_leader_arrival(step, pid)

    # single-frame hop (FRAMES_HOP_SYNC == 1)
    state[pid]["pos"] = leader_end
    for fpid, _fs, fend, _np in planned_followers:
        state[fpid]["pos"] = fend

    state[pid]["place"] = ("pane", step)
    revealed_safe_draw[step] = True
    for fpid, _s, _e, new_place in planned_followers:
        state[fpid]["place"] = new_place
        if new_place[0] == "pane":
            revealed_safe_draw[new_place[1]] = True

    if capture:
        snapshot(f"Step {step} safe {safe_side[step]} • Leader {pid}")

def leader_break_and_fall(pid, break_step, break_side, cause_note=""):
    # let followers advance up to (break_step-1) as part of the failing hop (no retighten)
    planned_followers = plan_followers_after_leader_arrival(break_step, pid)

    # leader to wrong pane (single frame)
    state[pid]["pos"] = pane_center(break_step, break_side)
    for fpid, _fs, fend, _np in planned_followers:
        state[fpid]["pos"] = fend
    for fpid, _s, _e, new_place in planned_followers:
        state[fpid]["place"] = new_place
        if new_place[0] == "pane":
            revealed_safe_draw[new_place[1]] = True
    snapshot(f"WRONG {break_step}{break_side} • Leader {pid}", cause_note)

    # pane breaks & fall
    broken_panes.add((break_step, break_side))
    x0, y0 = state[pid]["pos"]
    for k in range(FRAMES_FALL):
        t = (k+1)/FRAMES_FALL
        state[pid]["pos"] = (x0, y0 - 0.40*t)
        snapshot(f"Leader {pid} FELL at {break_step}{break_side}", cause_note)
    state[pid]["alive"] = False
    state[pid]["visible"] = False

def leader_fall_no_glass(pid, cause_note="ELIMINATED"):
    x0, y0 = state[pid]["pos"]
    for k in range(FRAMES_FALL):
        t = (k+1)/FRAMES_FALL
        state[pid]["pos"] = (x0, y0 - 0.40*t)
        snapshot(f"Leader {pid} {cause_note}", cause_note)
    state[pid]["alive"] = False
    state[pid]["visible"] = False

def leader_push_out(pid, cause_note="PUSHED OUT"):
    # push from Start only
    state[pid]["pos"] = (X0 - 0.10, Ymid)
    snapshot(f"Leader {pid} {cause_note}", cause_note)
    state[pid]["alive"]   = False
    state[pid]["visible"] = False

# ---------- VALIDATION: ensure leader already on a pane before capturing ----------
def ensure_ready_for_capture(pid):
    """
    If the next leader is still at Start, silently hop Start→step 1 (no frames).
    Then the rest of the turn will be captured normally.
    """
    loc, st = state[pid]["place"]
    if loc == "start":
        hop_with_queue(pid, 1, capture=False)  # silent; no frames

# ---------- Turn Runner ----------
def run_turn(pid, idx, result):
    # VALIDATE readiness
    ensure_ready_for_capture(pid)

    # show a tiny pause only if already on a pane
    loc, st = state[pid]["place"]
    if loc == "pane":
        for _ in range(FRAMES_PAUSE):
            snapshot(f"Turn {idx+1} • Player {pid} ready (from step {st})")

    cur_step = st if loc == "pane" else 0

    if result.lower().startswith("survived"):
        for s in range(cur_step+1, N_STEPS+1):
            hop_with_queue(pid, s, capture=True)
        # exit (single frame per setting)
        state[pid]["pos"] = end_pos
        snapshot(f"Turn {idx+1} • {pid} exit")
        state[pid]["finished"] = True
        state[pid]["place"]    = ("end", None)
        return {"turn": idx+1, "player": pid, "result":"Survived Stage", "cause":"Survived crossing", "fail_step": None}

    # Eliminated
    if pid == 322:
        leader_push_out(pid, cause_by_pid.get(pid, "PUSHED OUT"))
        return {"turn": idx+1, "player": pid, "result":"Eliminated", "cause":cause_by_pid.get(pid,"Pushed out"), "fail_step": None}

    if pid in broken_by_pid:
        bstep, bside = broken_by_pid[pid]
        for s in range(cur_step+1, bstep):
            hop_with_queue(pid, s, capture=True)
        leader_break_and_fall(pid, bstep, bside, cause_by_pid.get(pid,"Fell through glass"))
        return {"turn": idx+1, "player": pid, "result":"Eliminated", "cause":cause_by_pid.get(pid,"Fell through glass"), "fail_step": bstep}

    # Fallback elimination (e.g., 360)
    leader_fall_no_glass(pid, cause_by_pid.get(pid, "ELIMINATED"))
    return {"turn": idx+1, "player": pid, "result":"Eliminated", "cause":cause_by_pid.get(pid,"No glass break"), "fail_step": None}

# ---------- Build storyboard ----------
# (optional) tiny initial snapshot
snapshot("All players ready at Start")

outcomes = []
for idx, (turn, pid, result) in enumerate(turn_order):
    if not state[pid]["alive"]:
        continue
    outcomes.append(run_turn(pid, idx, result))

# ---------- Draw / Animate ----------
def refresh_panes(pane_safe, pane_broken):
    for rect in pane_patches.values():
        rect.set_facecolor(PANE); rect.set_alpha(1.0); rect.set_edgecolor(EDGE); rect.set_linewidth(1.0)
    for s in pane_safe:
        pane_patches[(s, safe_side[s])].set_facecolor(SAFE); pane_patches[(s, safe_side[s])].set_alpha(0.9)
    for (s, side) in pane_broken:
        pane_patches[(s, side)].set_facecolor(FAIL); pane_patches[(s, side)].set_alpha(0.9)

def update(i):
    fr = frames[i]
    refresh_panes(fr["pane_safe"], fr["pane_broken"])
    status_text.set_text(fr["status"])
    cause_text.set_text(fr["cause"])
    for pid in pids:
        x, y, vis = fr["players"][pid]
        dots[pid].set_data([x],[y])
        labels[pid].set_position((x, y+0.035))
        labels[pid].set_text(str(pid))
        dots[pid].set_visible(vis); labels[pid].set_visible(vis)
    return list(dots.values()) + list(labels.values()) + list(pane_patches.values()) + [status_text, cause_text]

FPS = 1
ani = animation.FuncAnimation(fig, update, frames=len(frames), interval=1000/FPS, blit=False, repeat=False)
out_gif = "game5_queue_validated.gif"
ani.save(out_gif, writer="pillow", fps=FPS)
print("Saved GIF:", out_gif)

# ---------- CSV outputs ----------
broken_list = sorted([(s, side) for (s, side) in broken_panes], key=lambda x:x[0])
pd.DataFrame(broken_list, columns=["step","side"]).to_csv("game5_broken_panes.csv", index=False)
pd.DataFrame(outcomes).to_csv("game5_outcomes.csv", index=False)
print("Saved CSVs: game5_broken_panes.csv, game5_outcomes.csv")
