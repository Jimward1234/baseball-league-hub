import streamlit as st
import os
import time
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION (Paste your keys here!) ---
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
    .profile-pic { border-radius: 50%; object-fit: cover; border: 2px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS (The "Brain") ---
def get_public_url(path):
    """Gets the permanent link for an uploaded image or song."""
    return supabase.storage.from_('uploads').get_public_url(path)

def save_file_to_supabase(file, path):
    """Uploads a file to your Supabase 'uploads' bucket."""
    supabase.storage.from_('uploads').upload(path, file, {"upsert": "true"})
    return get_public_url(path)

# --- 4. AUTHENTICATION & LOGIN ---
if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("⚾ League Hub")
    choice = st.radio("Select Action", ["Login", "Join a League", "Create a League"], horizontal=True)

    if choice == "Create a League":
        st.subheader("🛡️ Create New League")
        new_l = st.text_input("League Name").strip().upper()
        email = st.text_input("Admin Email (This is your username)")
        pwd = st.text_input("Password", type="password")
        
        if st.button("Initialize My League"):
            try:
                # 1. Create the user in Supabase Auth
                res = supabase.auth.sign_up({"email": email, "password": pwd})
                # 2. Save league details to a table
                supabase.table('leagues').insert({"name": new_l, "admin_email": email}).execute()
                st.success("League created! Check your email to confirm, then Login.")
            except Exception as e: st.error(f"Error: {e}")

    elif choice == "Login":
        email = st.text_input("Email")
        pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": pwd})
                # Get user profile data
                profile = supabase.table('profiles').select("*").eq('email', email).single().execute()
                st.session_state.user = profile.data
                st.rerun()
            except: st.error("Login failed. Check email/password.")
        
        if st.button("Forgot Password?"):
            supabase.auth.reset_password_for_email(email)
            st.info("Reset link sent to your email!")

# --- 5. MAIN APP INTERFACE ---
else:
    u = st.session_state.user
    l_name = u["league"]
    
    st.sidebar.title(f"👋 {u['username']}")
    if u.get('avatar_url'):
        st.sidebar.image(u['avatar_url'], width=100)
    
    st.sidebar.info(f"League: {l_name} | Role: {u['role']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # --- TABS: ADAPTIVE BASED ON ROLE ---
    main_tabs = ["🎙️ Game Deck", "⚙️ Manage League", "👤 My Profile"] if u['role'] == "Announcer" else ["💎 Field", "📋 Team", "👤 My Profile"]
    tabs = st.tabs(main_tabs)

    # --- PROFILE TAB (Works for Everyone) ---
    with tabs[-1]:
        st.header("👤 My Player Profile")
        col1, col2 = st.columns(2)
        
        with col1:
            new_num = st.text_input("Player / Staff #", value=u.get('player_number', ''))
            new_pic = st.file_uploader("Update Profile Picture", type=['png', 'jpg'])
            if st.button("Save Profile Basics"):
                update_data = {"player_number": new_num}
                if new_pic:
                    pic_path = f"avatars/{u['email']}.png"
                    url = save_file_to_supabase(new_pic.getvalue(), pic_path)
                    update_data["avatar_url"] = url
                supabase.table('profiles').update(update_data).eq('email', u['email']).execute()
                st.success("Profile Updated!")

        with col2:
            st.subheader("🎵 Walk-Up Song")
            new_song = st.file_uploader("Upload .mp3", type=['mp3'])
            if st.button("Save Song"):
                if new_song:
                    song_path = f"songs/{u['email']}.mp3"
                    url = save_file_to_supabase(new_song.getvalue(), song_path)
                    supabase.table('profiles').update({"walkup_url": url}).eq('email', u['email']).execute()
                    st.success("Song Saved!")

    # --- COACH SPECIFIC: TEAM LOGO ---
    if u['role'] == "Coach":
        with tabs[1]:
            st.subheader("🏆 Team Branding")
            team_logo = st.file_uploader("Upload Team Logo", type=['png', 'jpg'])
            if st.button("Save Team Logo"):
                if team_logo:
                    logo_path = f"logos/{u['team']}.png"
                    url = save_file_to_supabase(team_logo.getvalue(), logo_path)
                    supabase.table('teams').update({"logo_url": url}).eq('name', u['team']).execute()
                    st.success("Logo Updated for everyone to see!")

    # --- ANNOUNCER VIEW: LOGOS & SONGS ---
    if u['role'] == "Announcer":
        with tabs[0]:
            # Logic to pull Team Logos from Supabase
            # If team has logo, display: st.image(team_logo_url, width=50)
            # Logic to play walkup_url from player profile
            st.write("Game Deck is now connected to live Supabase data.")
            # [Previous Game Deck logic goes here, but pulling from supabase tables]
