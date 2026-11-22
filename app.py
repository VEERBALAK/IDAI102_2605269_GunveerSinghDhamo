"""MedTimer - a friendly medicine reminder app for elderly people.

Built with Streamlit. The reward artwork (smiley / trophy) is drawn
with Turtle graphics - see turtle_art.py.
"""

import base64
import datetime as dt
import json
import os
import subprocess
import sys
import uuid

import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "medtimer_data.json")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

GRACE = dt.timedelta(hours=1)  # a due dose turns red this long after its time

QUOTES = [
    "Every dose you take is a small victory. Keep going!",
    "Taking your medicine on time is a gift to your future self.",
    "You are doing something wonderful for your health today.",
    "One pill at a time, one day at a time. You've got this!",
    "Your family loves seeing you healthy and strong.",
    "Small habits, big health. Well done for showing up today!",
    "A healthy routine is the best present you can give yourself.",
]

CSS = """
<style>
.stApp { background-color: #F6F9F4; }
html, body, [class*="css"] { font-size: 21px; color: #2F3E33; }
h1 { color: #2E5E4E; font-size: 2.6rem !important; }
h2, h3 { color: #2E5E4E; }
.dose-time { border-radius: 14px; padding: 14px 6px; text-align: center;
             font-size: 1.25rem; font-weight: 700; }
.dose-card { border-radius: 14px; padding: 12px 16px; font-size: 1.1rem; }
.dose-sub { color: #5b6b60; font-size: 0.95rem; }
.score { font-size: 3rem; font-weight: 800; color: #2E5E4E; text-align: center; }
.stButton button { font-size: 1.05rem; border-radius: 12px; }
</style>
"""


# ------------------------------------------------------------------ data ----
def load_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"medicines": [], "log": {}}


def save_data(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def dose_key(med_id, dose_time):
    return f"{med_id}|{dose_time}"


def todays_doses(meds):
    """Every scheduled dose, as (medicine, time_str), sorted by time."""
    doses = [(med, t) for med in meds for t in med["times"]]
    return sorted(doses, key=lambda d: d[1])


def weekly_totals(data, today, now):
    """Doses taken vs doses due so far over the last 7 days."""
    taken = due = 0
    for i in range(7):
        day = today - dt.timedelta(days=i)
        day_log = data["log"].get(day.isoformat(), {})
        for med, t in todays_doses(data["medicines"]):
            dose_dt = dt.datetime.combine(day, dt.time.fromisoformat(t))
            if day == today and dose_dt > now:
                continue  # still upcoming, not due yet
            due += 1
            if day_log.get(dose_key(med["id"], t)) == "taken":
                taken += 1
    return taken, due


def reward_image(score_pct):
    """Path to the turtle-drawn reward image for a high weekly score."""
    name = "trophy" if score_pct >= 100 else "smiley"
    path = os.path.join(ASSETS_DIR, name + ".png")
    if not os.path.exists(path):
        # Draw it live with Turtle graphics (needs ghostscript + a display).
        try:
            subprocess.run(
                [sys.executable, os.path.join(BASE_DIR, "turtle_art.py")],
                check=True, capture_output=True,
            )
        except Exception:
            return None
    return path if os.path.exists(path) else None


def play_beep():
    """Autoplay a gentle beep (used when the sound setting is on)."""
    beep = os.path.join(ASSETS_DIR, "beep.wav")
    if not os.path.exists(beep):
        return
    with open(beep, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    st.markdown(
        f'<audio autoplay="true"><source src="data:audio/wav;base64,{b64}"></audio>',
        unsafe_allow_html=True,
    )


# -------------------------------------------------------------------- UI ----
st.set_page_config(page_title="MedTimer", page_icon="💊", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)

data = load_data()
now = dt.datetime.now()
today = now.date()
meds = data["medicines"]
day_log = data["log"].setdefault(today.isoformat(), {})

st.title("💊 MedTimer")
st.caption("Your friendly medicine companion")
st.info("🌿 " + QUOTES[today.toordinal() % len(QUOTES)])

with st.sidebar:
    st.header("Settings")
    st.checkbox("🔔 Play a sound when a dose is due", key="sound_on")

# ------------------------------------------------------- today's checklist ----
st.header("Today's medicines")
if not meds:
    st.write("No medicines yet. Add your first one below! 👇")
else:
    due_now = []
    for med, t in todays_doses(meds):
        key = dose_key(med["id"], t)
        status = day_log.get(key)
        dose_dt = dt.datetime.combine(today, dt.time.fromisoformat(t))
        if status == "taken":
            color, label = "#DFF0D8", "✅ Taken"
        elif status == "missed":
            color, label = "#F2DEDE", "❌ Missed"
        elif now > dose_dt + GRACE:
            color, label = "#F2DEDE", "❌ Missed"
        elif now >= dose_dt:
            color, label = "#FCF8E3", "🟡 Due now"
            due_now.append((med, t))
        else:
            color, label = "#EEF3F8", "Upcoming"

        c_time, c_card, c_btn = st.columns([1, 3, 2])
        sub = med.get("dose", "")
        if med.get("notes"):
            sub += " · " + med["notes"]
        c_time.markdown(
            f'<div class="dose-time" style="background:{color}">{t}</div>',
            unsafe_allow_html=True,
        )
        c_card.markdown(
            f'<div class="dose-card" style="background:{color}">'
            f"<b>{med['name']}</b><br>"
            f'<span class="dose-sub">{sub} · {label}</span></div>',
            unsafe_allow_html=True,
        )
        if status != "taken":
            if c_btn.button("Taken ✔", key=f"take_{key}"):
                day_log[key] = "taken"
                save_data(data)
                st.rerun()
        else:
            if c_btn.button("Undo", key=f"undo_{key}"):
                del day_log[key]
                save_data(data)
                st.rerun()

    if due_now:
        names = ", ".join(f"{m['name']} at {t}" for m, t in due_now)
        st.warning(f"⏰ Time for: {names}")
        if st.session_state.get("sound_on"):
            play_beep()

# ------------------------------------------------------------ weekly score ----
st.header("Your week")
taken, due = weekly_totals(data, today, now)
score = round(100 * taken / due) if due else 0
st.progress(score / 100)
st.markdown(f"<div class='score'>{score}%</div>", unsafe_allow_html=True)
if due:
    st.write(f"You took {taken} of {due} doses this week.")
    if score >= 100:
        img = reward_image(score)
        if img:
            st.image(img, width=230)
        st.success("🏆 A perfect week! You took every single dose. Champion!")
    elif score >= 80:
        img = reward_image(score)
        if img:
            st.image(img, width=230)
        st.success("Wonderful work! You're doing great, keep it up! 🎉")
    elif score >= 50:
        st.info("Good effort! Try to take each dose at its time. You can do it! 💪")
    else:
        st.warning("Let's build the habit together. One dose at a time! 🌱")

# ------------------------------------------------------------ add medicine ----
st.header("Add a medicine")
with st.form("add_med", clear_on_submit=True):
    name = st.text_input("Medicine name", placeholder="e.g. Vitamin D")
    dose = st.text_input("Dose", placeholder="e.g. 1 tablet · 500 mg")
    n_times = st.selectbox("How many times a day?", [1, 2, 3, 4])
    times = [
        st.time_input(f"Time {i + 1}", dt.time(8 + i * 6))
        for i in range(n_times)
    ]
    notes = st.text_input("Notes (optional)", placeholder="e.g. after breakfast")
    if st.form_submit_button("Add medicine ➕"):
        if name.strip():
            meds.append({
                "id": uuid.uuid4().hex[:8],
                "name": name.strip(),
                "dose": dose.strip(),
                "times": sorted(t.strftime("%H:%M") for t in times),
                "notes": notes.strip(),
            })
            save_data(data)
            st.success(f"{name.strip()} added!")
            st.rerun()
        else:
            st.error("Please enter a medicine name.")

# ---------------------------------------------------------- edit / delete ----
if meds:
    st.header("Edit or remove")
    for med in meds:
        with st.expander(f"{med['name']} — {med.get('dose', '')}".rstrip(" —")):
            new_name = st.text_input("Name", med["name"], key=f"n_{med['id']}")
            new_dose = st.text_input("Dose", med.get("dose", ""), key=f"d_{med['id']}")
            new_times = [
                st.time_input(
                    f"Time {i + 1}", dt.time.fromisoformat(t),
                    key=f"t_{med['id']}_{i}",
                )
                for i, t in enumerate(med["times"])
            ]
            new_notes = st.text_input(
                "Notes", med.get("notes", ""), key=f"o_{med['id']}"
            )
            c_save, c_del = st.columns(2)
            if c_save.button("Save changes", key=f"s_{med['id']}"):
                med.update({
                    "name": new_name.strip() or med["name"],
                    "dose": new_dose.strip(),
                    "times": sorted(t.strftime("%H:%M") for t in new_times),
                    "notes": new_notes.strip(),
                })
                save_data(data)
                st.success("Saved!")
                st.rerun()
            if c_del.button("Delete 🗑", key=f"x_{med['id']}"):
                meds.remove(med)
                save_data(data)
                st.success(f"{med['name']} removed.")
                st.rerun()
