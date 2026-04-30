import streamlit as st
import os
import tempfile
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
SUPABASE_URL = "https://cdjjtomuokuluhvsjxpd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNkamp0b211b2t1bHVodnNqeHBkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzQ5Nzc3MywiZXhwIjoyMDkzMDczNzczfQ.waRifcTydbUakJIO7fHimlHT1Y8ifipi-gP6FIXlaFY" 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. MOVIEPY IMPORT ---
try:
    from moviepy.editor import AudioFileClip
except ImportError:
    st.error("⚠️ MoviePy not found. Please ensure it is in requirements.txt.")

# --- 3. THEME & STYLING ---
st.set_page_config(page_title="League Hub", layout="wide")

st.markdown("""
    <style>
    .stAudio { width: 100% !important; }
    .main-header { font-size: 2.5rem; font-weight: bold; color: white; }
    .field-container {
        position: relative;
        background-color: #2e7d32;
        border: 5px solid #5d4037;
        border-radius: 50% 50% 10px 10px;
        width: 100%;
        height: 500px;
        margin: auto;
        overflow: hidden;
    }
    .dirt-path {
        position: absolute;
        bottom: 0; left: 50%;
        transform: translateX(-50%);
        width: 300px; height: 300px;
        background-color: #8d6e63;
        rotate: 45deg;
        bottom: -150px;
    }
    .player-node {
        position: absolute;
        background: white;
        color: black;
        padding: 2px 8px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 0.8rem;
        text-align: center;
        border: 2px solid #ff4b4b;
        transform: translateX(-50%);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS ---
def save_file_to_supabase(file_bytes, path):
    try:
        supabase.storage.from_('uploads').upload(path, file_bytes, {"upsert": "true"})
        return supabase.storage.from_('uploads').get_public_url(path)
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None

def extract_audio_from_video(video_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_vid:
        temp_vid.write(video_file.read())
        temp_vid_path = temp_vid.name
    temp_audio_path = temp_vid_path.replace('.mp4', '.mp3')
    try:
        clip = AudioFileClip(temp_vid_path)
        clip.write_audiofile(temp_audio_path, logger=None)
        clip.close()
        with open(temp_audio_path, 'rb') as f:
            audio_bytes = f.read()
        os.remove(temp_vid_path)
        os.remove(temp_audio_path)
        return audio_bytes
    except Exception as e:
        st.error(f"Audio extraction failed: {e}")
        return None

def draw_diamond(roster_data):
    pos_map = {
        "CF": {"top": "10%", "left": "50%"},
        "LF": {"top": "25%", "left": "20%"},
        "RF": {"top": "25%", "left": "80%"},
        "SS": {"top": "45%", "left": "35%"},
        "2B": {"top": "45%", "left": "65%"},
        "3B": {"top": "65%", "left": "25%"},
        "1B": {"top": "65%", "left": "75%"},
        "P":  {"top": "60%", "left": "50%"},
        "C":  {"top": "85%", "left": "50%"},
    }
    field_html = '<div class="field-container"><div class="dirt-path"></div>'
    for player in roster_data:
        pos = player.get("position")
        if pos in pos_map:
            coords = pos_map[pos]
            name = player.get("username", "Empty")
            field_html += f'<div class="player-node" style="top:{coords["top"]}; left:{coords["left"]};">{pos}: {name}</div>'
    field_html += '</div>'
    st.markdown(field_html, unsafe_allow_html=True)

# --- 5. AUTHENTICATION ---
if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("⚾ League Hub")
    choice = st.radio("Action", ["Login", "Join", "Create", "Forgot Password"], horizontal=True)
    
    if choice == "Login":
        l_email = st.text_input("Email")
        l_pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": l_email, "password": l_pwd})
                if res.user:
                    p = supabase.table('profiles').select("*").eq('email', l_email).single().execute()
                    st.session_state.user = p.data
                    st.rerun()
            except Exception as e:
                st.error("Login failed. Check your credentials.")

    elif choice == "Forgot Password":
        f_email = st.text_input("Enter your account email")
        if st.button("Send Reset Link"):
            try:
                supabase.auth.reset_password_for_email(f_email)
                st.success("Reset link sent! Check your inbox.")
            except Exception as e:
                st.error("Error sending reset link.")

    elif choice == "Create":
        st.subheader("🛡️ Initialize New League")
        new_l = st.text_input("League Name").strip().upper()
        new_code = st.text_input("Join Code").strip()
        email = st.text_input("Admin Email")
        pwd = st.text_input("Password", type="password")
        u_name = st.text_input("Admin Full Name")
        if st.button("Initialize League"):
            try:
                supabase.auth.sign_up({"email": email, "password": pwd})
                supabase.table('leagues').insert({"name": new_l, "join_code": new_code, "admin_email": email}).execute()
                supabase.table('profiles').update({"username": u_name, "role": "Announcer", "league": new_l}).eq('email', email).execute()
                st.success("League created! Please log in.")
            except Exception as e: st.error(f"Setup Error: {e}")

    elif choice == "Join":
        st.subheader("🔑 Join Existing League")
        input_code = st.text_input("Enter Invite Code").strip()
        if st.button("Verify Code"):
            match = supabase.table('leagues').select("name").eq('join_code', input_code).execute()
            if match.data:
                st.session_state.found_league = match.data[0]['name']
                teams_q = supabase.table('teams').select("name").eq('league', st.session_state.found_league).execute()
                st.session_state.league_teams = [t['name'] for t in teams_q.data]
                st.success(f"Verified for {st.session_state.found_league}")

        if 'found_league' in st.session_state:
            st.divider()
            reg_email = st.text_input("Email")
            reg_pwd = st.text_input("Password", type="password")
            reg_name = st.text_input("Full Name")
            reg_role = st.selectbox("Role", ["Player", "Coach"])
            sel_team = st.selectbox("Select Team", options=st.session_state.get('league_teams', []))
            if st.button("Complete Sign Up"):
                try:
                    supabase.auth.sign_up({"email": reg_email, "password": reg_pwd})
                    supabase.table('profiles').update({
                        "username": reg_name, "role": reg_role, 
                        "league": st.session_state.found_league, "team": sel_team
                    }).eq('email', reg_email).execute()
                    st.success("Registration successful! Please log in.")
                except Exception as e: st.error(f"Error: {e}")

# --- 6. DASHBOARD ---
else:
    u = st.session_state.user
    l_name = u.get("league", "General")
    my_team = u.get("team", "Unassigned")
    
    st.sidebar.title(f"👤 {u.get('username')}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    if u.get('role') == "Announcer":
        tabs = st.tabs(["🎙️ Game Deck", "⚙️ Manage", "👤 Profile"])
        with tabs[0]:
            st.header("Live Game Deck")
            teams_q = supabase.table('teams').select("name").eq('league', l_name).execute()
            team_list = [t['name'] for t in teams_q.data]
            c1, c2 = st.columns(2)
            with c1:
                t1 = st.selectbox("Away Team", team_list)
                t1_players = supabase.table('profiles').select("*").eq('team', t1).execute().data
                draw_diamond(t1_players)
                for p in t1_players:
                    col_a, col_b = st.columns([3,1])
                    col_a.write(f"{p['username']} ({p.get('position', 'Sub')})")
                    if p.get('walkup_url') and col_b.button("🎵", key=f"play_t1_{p['email']}"):
                        st.audio(p['walkup_url'])
            with c2:
                t2 = st.selectbox("Home Team", team_list)
                t2_players = supabase.table('profiles').select("*").eq('team', t2).execute().data
                draw_diamond(t2_players)
                for p in t2_players:
                    col_a, col_b = st.columns([3,1])
                    col_a.write(f"{p['username']} ({p.get('position', 'Sub')})")
                    if p.get('walkup_url') and col_b.button("🎵", key=f"play_t2_{p['email']}"):
                        st.audio(p['walkup_url'])

    elif u.get('role') == "Coach":
        tabs = st.tabs([f"📋 {my_team} Management", "👤 Profile"])
        with tabs[0]:
            players_q = supabase.table('profiles').select("*").eq('team', my_team).execute()
            roster = players_q.data
            col_list, col_field = st.columns([1, 2])
            with col_list:
                st.subheader("Assign Positions")
                for p in roster:
                    current_pos = p.get('position', 'Sub')
                    pos_options = ["Sub", "P", "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]
                    try:
                        idx = pos_options.index(current_pos)
                    except ValueError:
                        idx = 0
                    
                    new_pos = st.selectbox(f"{p['username']}", pos_options, index=idx, key=f"pos_coach_{p['email']}")
                    if new_pos != current_pos:
                        try:
                            # This is the specific line that was causing the crash
                            supabase.table('profiles').update({"position": new_pos}).eq('email', p['email']).execute()
                            st.rerun()
                        except Exception as e:
                            st.warning("⚠️ Database Update Failed: Check your Supabase RLS Policies.")
            with col_field:
                draw_diamond(roster)

    else:
        tabs = st.tabs(["💎 Game View", "👤 Profile"])
        with tabs[0]:
            st.header(f"Team: {my_team}")
            roster = supabase.table('profiles').select("*").eq('team', my_team).execute().data
            draw_diamond(roster)
        with tabs[1]:
            st.header("Profile & Walk-up")
            media = st.file_uploader("Upload Walk-up (Video or Audio)", type=['mp3', 'mp4', 'mov', 'avi'])
            if st.button("Save Walk-Up"):
                if media:
                    with st.spinner("Processing..."):
                        ext = media.name.split('.')[-1].lower()
                        audio_data = extract_audio_from_video(media) if ext in ['mp4', 'mov', 'avi'] else media.read()
                        if audio_data:
                            url = save_file_to_supabase(audio_data, f"songs/{u['email']}.mp3")
                            supabase.table('profiles').update({"walkup_url": url}).eq('email', u['email']).execute()
                            st.success("Saved!")
