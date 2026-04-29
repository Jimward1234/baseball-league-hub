import streamlit as st
import os
import json
import time

# --- MoviePy Robust Import ---
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip
    except ImportError:
        VideoFileClip = None 

# --- 1. SETUP & THEME ---
st.set_page_config(page_title="League Hub", layout="wide")

st.markdown("""
    <style>
    .stAudio { width: 100% !important; }
    audio { height: 45px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    .pos-box { background-color: #1f2937; padding: 10px; border-radius: 10px; text-align: center; border: 1px solid #374151; margin-bottom: 5px; min-height: 60px; }
    .team-header { padding: 10px; background-color: #0e1117; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

for folder in ["songs", "data", "temp_video"]:
    if not os.path.exists(folder): os.makedirs(folder)

# --- 2. DATA STORAGE ---
def load_db(name):
    path = f"data/{name}.json"
    if os.path.exists(path):
        with open(path, "r") as f: return json.load(f)
    return {}

def save_db(name, data):
    with open(f"data/{name}.json", "w") as f: json.dump(data, f)

# --- 3. AUTHENTICATION & GATEWAY ---
if 'user' not in st.session_state: st.session_state.user = None
if 'reg_league' not in st.session_state: st.session_state.reg_league = None

registry = load_db("league_registry")

if st.session_state.user is None:
    st.title("⚾ League Hub")
    choice = st.radio("Select Action", ["Login", "Join a League", "Create a League"], horizontal=True)

    if choice == "Create a League":
        st.subheader("🛡️ League Founder & Announcer Setup")
        new_l = st.text_input("League Name").strip().upper()
        new_c = st.text_input("Create Join Code (for others)").strip()
        adm_u = st.text_input("Admin Username").strip()
        adm_p = st.text_input("Admin Password", type="password")
        
        if st.button("Initialize My League"):
            if new_l and new_c and adm_u and adm_p:
                if new_l in registry:
                    st.error("League name already exists.")
                else:
                    registry[new_l] = new_c
                    save_db("league_registry", registry)
                    users = load_db("users")
                    users[f"{new_l}_ADMIN_{adm_u}"] = {
                        "pass": adm_p, "role": "Announcer", "team": "LEAGUE_ADMIN", "league": new_l, "username": adm_u
                    }
                    save_db("users", users)
                    st.success(f"League '{new_l}' created! Login as Admin.")
            else: st.error("Fill out all fields.")

    elif choice == "Join a League":
        if not st.session_state.reg_league:
            st.subheader("🔑 Join Existing League")
            target_l = st.text_input("League Name").strip().upper()
            target_c = st.text_input("League Join Code", type="password")
            if st.button("Verify Code"):
                if target_l in registry and registry[target_l] == target_c:
                    st.session_state.reg_league = target_l
                    st.rerun()
                else: st.error("Invalid credentials.")
        else:
            l_name = st.session_state.reg_league
            st.subheader(f"📝 Registering for {l_name}")
            role = st.selectbox("Role", ["Player", "Coach"])
            l_data = load_db(f"settings_{l_name}")
            l_teams = l_data.get("teams", [])
            
            if not l_teams:
                st.warning("The Announcer hasn't created any teams yet.")
            else:
                t_name = st.selectbox("Select Team", l_teams)
                u_name = st.text_input("Your Name").strip()
                pwd = st.text_input("Password", type="password")
                if st.button("Sign Up"):
                    users = load_db("users")
                    uid = f"{l_name}_{t_name}_{u_name}"
                    users[uid] = {"pass": pwd, "role": role, "team": t_name, "league": l_name, "username": u_name}
                    save_db("users", users)
                    r_db = load_db(f"roster_{l_name}_{t_name}")
                    plist = r_db.get("players", [])
                    if u_name not in plist:
                        plist.append(u_name)
                        r_db["players"] = plist
                        save_db(f"roster_{l_name}_{t_name}", r_db)
                    st.success("Registration complete! Please Login.")
                    st.session_state.reg_league = None
            if st.button("Back"): st.session_state.reg_league = None; st.rerun()

    else:
        l_name = st.text_input("League Name").strip().upper()
        u_name = st.text_input("Username").strip()
        pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            all_u = load_db("users")
            match = None
            for key, val in all_u.items():
                if val.get("league") == l_name and val.get("username") == u_name and val.get("pass") == pwd:
                    match = val
                    break
            if match:
                st.session_state.user = match
                st.rerun()
            else: st.error("Login failed.")

else:
    u = st.session_state.user
    l_name = u["league"]
    st.sidebar.title(f"👋 {u['username']}")
    st.sidebar.info(f"League: {l_name}\nRole: {u['role']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    def draw_diamond(league, team):
        lineup = load_db(f"lineup_{league}_{team}")
        st.markdown(f"<div class='team-header'><h3>🛡️ {team} Defense</h3></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c2: st.markdown(f"<div class='pos-box'>CF<br><b>{lineup.get('CF', '---')}</b></div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='pos-box'>LF<br><b>{lineup.get('LF', '---')}</b></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='pos-box'>SS<br><b>{lineup.get('SS', '---')}</b></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='pos-box'>2B<br><b>{lineup.get('2B', '---')}</b></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='pos-box'>RF<br><b>{lineup.get('RF', '---')}</b></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"<div class='pos-box'>3B<br><b>{lineup.get('3B', '---')}</b></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='pos-box'>P<br><b>{lineup.get('P', '---')}</b></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='pos-box'>1B<br><b>{lineup.get('1B', '---')}</b></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c2: st.markdown(f"<div class='pos-box'>C<br><b>{lineup.get('C', '---')}</b></div>", unsafe_allow_html=True)

    def draw_order(league, team):
        order = load_db(f"order_{league}_{team}").get("order", [])
        st.write(f"**🔢 {team} Batting Order**")
        if any(p != "Empty" for p in order):
            for i, p in enumerate(order):
                if p != "Empty": st.write(f"{i+1}. {p}")
        else: st.caption("No order set.")

    if u['role'] == "Announcer":
        tabs = st.tabs(["🎙️ Game Deck", "⚙️ Manage League"])
        l_settings = load_db(f"settings_{l_name}")
        teams = l_settings.get("teams", [])

        with tabs[0]:
            col1, col2 = st.columns(2)
            t_a = col1.selectbox("Away", ["Select"] + teams)
            t_b = col2.selectbox("Home", ["Select"] + teams)
            if t_a != "Select" and t_b != "Select":
                ca, cb = st.columns(2)
                for t, col in [(t_a, ca), (t_b, cb)]:
                    with col:
                        draw_diamond(l_name, t)
                        st.divider()
                        order = load_db(f"order_{l_name}_{t}").get("order", [])
                        times = load_db(f"times_{l_name}_{t}")
                        for i, p in enumerate(order):
                            if p != "Empty":
                                if st.button(f"🎵 {p}", key=f"ann_{t}_{i}"):
                                    path = f"songs/{l_name}_{t}_{p}.mp3"
                                    if os.path.exists(path): st.audio(path, start_time=int(times.get(p, 0)), autoplay=True)
                if st.button("🛑 STOP AUDIO", type="primary"): st.rerun()

        with tabs[1]:
            st.header("Teams")
            new_t = st.text_input("New Team").upper().strip()
            if st.button("Add Team"):
                if new_t and new_t not in teams:
                    teams.append(new_t)
                    l_settings["teams"] = teams
                    save_db(f"settings_{l_name}", l_settings)
                    st.success(f"Added {new_t} to the league!")
                    st.rerun()
            for t in teams:
                c1, c2 = st.columns([4, 1])
                c1.info(f"⚾ {t}")
                if c2.button("🗑️", key=f"del_{t}"):
                    teams.remove(t); l_settings["teams"] = teams
                    save_db(f"settings_{l_name}", l_settings); st.rerun()

    else:
        team = u["team"]
        role_tabs = ["💎 Field/Order", "🔊 Soundboard", "📋 Roster", "⚾ Edit Lineup", "📤 My Song"] if u['role'] == "Coach" else ["💎 Field/Order", "📤 My Song"]
        tabs = st.tabs(role_tabs)
        
        with tabs[0]:
            draw_diamond(l_name, team)
            st.divider()
            draw_order(l_name, team)

        if u['role'] == "Coach":
            with tabs[1]:
                st.subheader("Walk-Ups")
                times = load_db(f"times_{l_name}_{team}")
                for f in os.listdir("songs"):
                    if f.startswith(f"{l_name}_{team}"):
                        p = f.replace(".mp3", "").split("_")[-1]
                        if st.button(f"Play {p}", key=f"sb_{p}"):
                            st.audio(f"songs/{f}", start_time=int(times.get(p, 0)), autoplay=True)
            with tabs[2]:
                rlist = load_db(f"roster_{l_name}_{team}").get("players", [])
                for pl in rlist: st.write(f"✅ {pl}")
            with tabs[3]:
                full_r = load_db(f"roster_{l_name}_{team}").get("players", [])
                st.subheader("Defense")
                curr_l = load_db(f"lineup_{l_name}_{team}")
                new_l = {}
                positions = ["P","C","1B","2B","3B","SS","LF","CF","RF"]
                cols = st.columns(3)
                for i, pos in enumerate(positions):
                    with cols[i%3]:
                        prev = curr_l.get(pos, "Empty")
                        idx = full_r.index(prev)+1 if prev in full_r else 0
                        new_l[pos] = st.selectbox(pos, ["Empty"] + full_r, index=idx, key=f"ed_{pos}")
                st.divider()
                st.subheader("Batting Order")
                curr_o = load_db(f"order_{l_name}_{team}").get("order", ["Empty"]*9)
                new_o = [st.selectbox(f"Batter {i+1}", ["Empty"] + full_r, index=(full_r.index(curr_o[i])+1 if i<len(curr_o) and curr_o[i] in full_r else 0), key=f"bat_{i}") for i in range(9)]
                if st.button("Save Changes"):
                    save_db(f"lineup_{l_name}_{team}", new_l)
                    save_db(f"order_{l_name}_{team}", {"order": new_o})
                    st.success("Lineup saved!")
            upload_tab = tabs[4]
        else:
            upload_tab = tabs[1]

        with upload_tab:
            st.subheader("🎵 My Walk-Up Settings")
            t_db = load_db(f"times_{l_name}_{team}")
            current_time = t_db.get(u['username'], 0)
            new_t = st.number_input("Start Time (seconds)", 0, 300, int(current_time), key="ts_update")
            if st.button("Update Timestamp Only"):
                t_db[u['username']] = new_t
                save_db(f"times_{l_name}_{team}", t_db)
                st.success(f"Start time updated to {new_t}s!")
            st.divider()
            up_f = st.file_uploader("Audio/Video", type=["mp3","mov","mp4"])
            if st.button("Upload New File"):
                if up_f:
                    f_p = f"songs/{l_name}_{team}_{u['username']}.mp3"
                    t_db[u['username']] = new_t
                    save_db(f"times_{l_name}_{team}", t_db)
                    if up_f.name.lower().endswith(('mov', 'mp4')) and VideoFileClip:
                        with st.status("Converting..."):
                            tmp = f"temp_video/{up_f.name}"
                            with open(tmp, "wb") as f: f.write(up_f.getbuffer())
                            with VideoFileClip(tmp) as clip: clip.audio.write_audiofile(f_p)
                            os.remove(tmp)
                    else:
                        with open(f_p, "wb") as f: f.write(up_f.getbuffer())
                    st.success("Saved!")
