import streamlit as st
import os
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
# Replace these with your actual keys from the Supabase Dashboard
SUPABASE_URL = "https://cdjjtomuokuluhvsjxpd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNkamp0b211b2t1bHVodnNqeHBkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0OTc3NzMsImV4cCI6MjA5MzA3Mzc3M30.oNrH9jmeyXxedj0NTRrhTilpGtOoPRZzy6SA5rsy16g"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- MoviePy Robust Import ---
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip
    except ImportError:
        VideoFileClip = None 

# --- 2. SETUP & THEME ---
st.set_page_config(page_title="League Hub", layout="wide")

st.markdown("""
    <style>
    .stAudio { width: 100% !important; }
    audio { height: 45px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    .pos-box { background-color: #1f2937; padding: 10px; border-radius: 10px; text-align: center; border: 1px solid #374151; margin-bottom: 5px; min-height: 60px; }
    .team-header { padding: 10px; background-color: #0e1117; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 15px; display: flex; align-items: center; gap: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def save_file_to_supabase(file_bytes, path):
    """Uploads a file to the 'uploads' bucket and returns the public URL."""
    supabase.storage.from_('uploads').upload(path, file_bytes, {"upsert": "true"})
    return supabase.storage.from_('uploads').get_public_url(path)

# --- 4. AUTHENTICATION & GATEWAY ---
if 'user' not in st.session_state: 
    st.session_state.user = None

if st.session_state.user is None:
    st.title("⚾ League Hub")
    choice = st.radio("Select Action", ["Login", "Join a League", "Create a League"], horizontal=True)

    if choice == "Create a League":
        st.subheader("🛡️ Create New League")
        new_l = st.text_input("League Name").strip().upper()
        new_code = st.text_input("Create a Join Code (e.g., BASEBALL26)").strip()
        email = st.text_input("Admin Email")
        pwd = st.text_input("Password", type="password", help="Minimum 6 characters")
        u_name = st.text_input("Your Full Name (Admin)")
        
        if st.button("Initialize My League"):
            if new_l and new_code and email and pwd:
                try:
                    # 1. Auth Signup
                    auth_res = supabase.auth.sign_up({"email": email, "password": pwd})
                    # 2. Create League entry
                    supabase.table('leagues').insert({
                        "name": new_l, 
                        "join_code": new_code, 
                        "admin_email": email
                    }).execute()
                    # 3. Update the Profile (Trigger creates the row, we update it)
                    supabase.table('profiles').update({
                        "username": u_name,
                        "role": "Announcer",
                        "league": new_l
                    }).eq('email', email).execute()
                    
                    st.success(f"League '{new_l}' initialized! Switch to Login tab.")
                except Exception as e:
                    st.error(f"Setup Error: {e}")
            else:
                st.error("Please fill in all fields.")

    elif choice == "Join a League":
        st.subheader("🔑 Join with Invite Code")
        input_code = st.text_input("Enter code from your Admin").strip()
        
        if st.button("Verify Code"):
            match = supabase.table('leagues').select("name").eq('join_code', input_code).execute()
            if match.data:
                st.session_state.found_league = match.data[0]['name']
                # Fetch teams specifically for this league
                team_query = supabase.table('teams').select("name").eq('league', st.session_state.found_league).execute()
                st.session_state.league_teams = [t['name'] for t in team_query.data]
                st.success(f"Joining: {st.session_state.found_league}")
            else:
                st.error("Invalid Code.")

        if 'found_league' in st.session_state:
            st.divider()
            reg_email = st.text_input("Email")
            reg_pwd = st.text_input("Password", type="password", help="Minimum 6 characters")
            reg_name = st.text_input("Your Full Name")
            reg_role = st.selectbox("Role", ["Player", "Coach"])
            
            if st.session_state.get('league_teams'):
                selected_team = st.selectbox("Select Your Team", options=st.session_state['league_teams'])
            else:
                st.warning("No teams found. Contact your Admin to add teams first.")
                selected_team = None
            
            if st.button("Complete Sign Up"):
                if not selected_team:
                    st.error("Team selection is required.")
                else:
                    try:
                        supabase.auth.sign_up({"email": reg_email, "password": reg_pwd})
                        supabase.table('profiles').update({
                            "username": reg_name,
                            "role": reg_role,
                            "league": st.session_state.found_league,
                            "team": selected_team
                        }).eq('email', reg_email).execute()
                        st.success(f"Registered for {selected_team}! Switch to Login tab.")
                    except Exception as e:
                        st.error(f"Registration Error: {e}")

    else:
        st.subheader("👋 Welcome Back")
        login_email = st.text_input("Email")
        login_pwd = st.text_input("Password", type="password")
        
        if st.button("Login"):
            try:
                auth_res = supabase.auth.sign_in_with_password({"email": login_email, "password": login_pwd})
                prof_res = supabase.table('profiles').select("*").eq('email', login_email).single().execute()
                st.session_state.user = prof_res.data
                st.rerun()
            except Exception:
                st.error("Login failed. Check your credentials.")

# --- 5. MAIN APP INTERFACE ---
else:
    u = st.session_state.user
    l_name = u.get("league", "General")
    my_team = u.get("team", "Unassigned")
    
    st.sidebar.title(f"👤 {u.get('username', 'User')}")
    st.sidebar.info(f"League: {l_name}\nTeam: {my_team}\nRole: {u.get('role')}")
    
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # --- Role-Based Dashboards ---
    if u.get('role') == "Announcer":
        tabs = st.tabs(["🎙️ Game Deck", "⚙️ Manage League", "👤 My Profile"])
        
        with tabs[0]:
            st.header("🎙️ Live Game Deck")
            st.info("Lineup will appear here once players join.")
            
        with tabs[1]:
            st.header("⚙️ League Management")
            t_name = st.text_input("New Team Name")
            if st.button("Add Team"):
                if t_name:
                    supabase.table('teams').insert({"name": t_name, "league": l_name}).execute()
                    st.success(f"Added {t_name}!")
                    st.rerun()
            
            st.subheader("Existing Teams")
            teams_res = supabase.table('teams').select("*").eq('league', l_name).execute()
            for t in teams_res.data:
                st.write(f"⚾ {t['name']}")

    elif u.get('role') == "Coach":
        tabs = st.tabs([f"📋 {my_team} Roster", "👤 My Profile"])
        with tabs[0]:
            st.header(f"📋 {my_team} Team Roster")
            players = supabase.table('profiles').select("*")\
                .eq('league', l_name)\
                .eq('role', 'Player')\
                .eq('team', my_team).execute()
            
            if players.data:
                for p in players.data:
                    c1, c2 = st.columns([1, 4])
                    c1.write(f"#{p.get('player_number', '??')}")
                    c2.write(f"**{p['username']}**")
            else:
                st.info(f"No players have joined the {my_team} yet.")

    else: # Player Role
        tabs = st.tabs(["💎 My Field View", "👤 My Profile"])
        with tabs[0]:
            st.header(f"💎 {my_team} Player Portal")
            st.write("Welcome to the team! Upload your walk-up song in 'My Profile'.")

    # --- SHARED: MY PROFILE TAB ---
    with tabs[-1]:
        st.header("Update My Info")
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            new_num = st.text_input("Player/Staff #", value=u.get('player_number', ''))
            if st.button("Save Profile"):
                supabase.table('profiles').update({"player_number": new_num}).eq('email', u['email']).execute()
                st.success("Profile Updated!")

        with p_col2:
            st.subheader("Walk-Up Song")
            new_song = st.file_uploader("Upload .mp3", type=['mp3'])
            if st.button("Save Song"):
                if new_song:
                    url = save_file_to_supabase(new_song.getvalue(), f"songs/{u['email']}.mp3")
                    supabase.table('profiles').update({"walkup_url": url}).eq('email', u['email']).execute()
                    st.success("Song Saved!")
