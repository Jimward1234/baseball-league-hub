import streamlit as st
import os
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
# Paste your actual keys from the Supabase Dashboard here
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
        pwd = st.text_input("Password", type="password")
        u_name = st.text_input("Your Full Name (Admin)")
        
        if st.button("Initialize My League"):
            if new_l and new_code and email and pwd:
                try:
                    # 1. Create Auth User
                    auth_res = supabase.auth.sign_up({"email": email, "password": pwd})
                    # 2. Save League & Admin Profile
                    supabase.table('leagues').insert({
                        "name": new_l, 
                        "join_code": new_code, 
                        "admin_email": email
                    }).execute()
                    
                    supabase.table('profiles').insert({
                        "email": email,
                        "username": u_name,
                        "role": "Announcer",
                        "league": new_l
                    }).execute()
                    
                    st.success(f"League '{new_l}' initialized! Check email to confirm, then login.")
                except Exception as e:
                    st.error(f"Setup Error: {e}")
            else:
                st.error("Please fill in all fields.")

    elif choice == "Join a League":
        st.subheader("🔑 Join with Invite Code")
        input_code = st.text_input("Enter the code provided by your Admin").strip()
        
        if st.button("Verify Code"):
            match = supabase.table('leagues').select("name").eq('join_code', input_code).execute()
            if match.data:
                st.session_state.found_league = match.data[0]['name']
                st.success(f"Code Verified! You are joining: {st.session_state.found_league}")
            else:
                st.error("Invalid Code. Please check with your Admin.")

        if 'found_league' in st.session_state:
            st.divider()
            st.info(f"Registering for {st.session_state.found_league}")
            reg_email = st.text_input("Email")
            reg_pwd = st.text_input("Create Password", type="password")
            reg_role = st.selectbox("Role", ["Player", "Coach"])
            reg_name = st.text_input("Your Full Name")
            
            if st.button("Complete Sign Up"):
                try:
                    supabase.auth.sign_up({"email": reg_email, "password": reg_pwd})
                    supabase.table('profiles').insert({
                        "email": reg_email,
                        "username": reg_name,
                        "role": reg_role,
                        "league": st.session_state.found_league
                    }).execute()
                    st.success("Registration successful! Verify your email then Login.")
                except Exception as e:
                    st.error(f"Registration Error: {e}")

    else:
        st.subheader("👋 Welcome Back")
        login_email = st.text_input("Email")
        login_pwd = st.text_input("Password", type="password")
        
        if st.button("Login"):
            try:
                auth_res = supabase.auth.sign_in_with_password({"email": login_email, "password": login_pwd})
                # Fetch their specific profile from the database
                prof_res = supabase.table('profiles').select("*").eq('email', login_email).single().execute()
                st.session_state.user = prof_res.data
                st.rerun()
            except Exception as e:
                st.error("Login failed. Check your email/password.")
        
        if st.button("Forgot Password?"):
            if login_email:
                supabase.auth.reset_password_for_email(login_email)
                st.info("Password reset link sent to your email.")
            else:
                st.warning("Please enter your email first.")

# --- 5. MAIN APP INTERFACE ---
else:
    u = st.session_state.user
    l_name = u["league"]
    
    st.sidebar.title(f"👤 {u['username']}")
    if u.get('avatar_url'):
        st.sidebar.image(u['avatar_url'], width=100)
    st.sidebar.info(f"League: {l_name}\nRole: {u['role']}")
    
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # --- Role-Based Tabs ---
    if u['role'] == "Announcer":
        tabs = st.tabs(["🎙️ Game Deck", "⚙️ Manage League", "👤 My Profile"])
    elif u['role'] == "Coach":
        tabs = st.tabs(["💎 Field/Order", "📋 Team Roster", "🏆 Team Logo", "👤 My Profile"])
    else:
        tabs = st.tabs(["💎 Field/Order", "👤 My Profile"])

    # --- SHARED: MY PROFILE TAB ---
    with tabs[-1]:
        st.header("Update My Info")
        col1, col2 = st.columns(2)
        with col1:
            new_num = st.text_input("Player/Staff #", value=u.get('player_number', ''))
            new_pic = st.file_uploader("Upload Profile Pic", type=['png', 'jpg'])
            if st.button("Save Profile"):
                updates = {"player_number": new_num}
                if new_pic:
                    url = save_file_to_supabase(new_pic.getvalue(), f"avatars/{u['email']}.png")
                    updates["avatar_url"] = url
                supabase.table('profiles').update(updates).eq('email', u['email']).execute()
                st.success("Saved!")

        with col2:
            st.subheader("Walk-Up Song")
            new_song = st.file_uploader("Upload Song (.mp3)", type=['mp3'])
            if st.button("Save Song"):
                if new_song:
                    url = save_file_to_supabase(new_song.getvalue(), f"songs/{u['email']}.mp3")
                    supabase.table('profiles').update({"walkup_url": url}).eq('email', u['email']).execute()
                    st.success("Song Saved!")
