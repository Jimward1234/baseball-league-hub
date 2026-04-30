import streamlit as st
import os
import tempfile
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
# Replace with your actual project credentials
SUPABASE_URL = "https://cdjjtomuokuluhvsjxpd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNkamp0b211b2t1bHVodnNqeHBkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0OTc3NzMsImV4cCI6MjA5MzA3Mzc3M30.oNrH9jmeyXxedj0NTRrhTilpGtOoPRZzy6SA5rsy16g"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. MOVIEPY IMPORT ---
try:
    from moviepy.editor import AudioFileClip
except ImportError:
    st.error("⚠️ MoviePy is not installed on this server. Please add 'moviepy' to your requirements.txt file and redeploy.")

# --- 3. THEME & STYLING ---
st.set_page_config(page_title="League Hub", layout="wide")

st.markdown("""
    <style>
    .stAudio { width: 100% !important; }
    audio { height: 45px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; color: white; background-color: #ff4b4b; }
    .stSidebar { background-color: #0e1117; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS ---
def save_file_to_supabase(file_bytes, path):
    """Uploads bytes directly to Supabase Storage."""
    supabase.storage.from_('uploads').upload(path, file_bytes, {"upsert": "true"})
    return supabase.storage.from_('uploads').get_public_url(path)

def extract_audio_from_video(video_file):
    """Strips audio from a video file and returns the MP3 bytes."""
    # 1. Save uploaded video to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_vid:
        temp_vid.write(video_file.read())
        temp_vid_path = temp_vid.name
    
    # 2. Define the path for the temporary audio output
    temp_audio_path = temp_vid_path.replace('.mp4', '.mp3')
    
    try:
        # 3. Use MoviePy to 'strip' the audio
        clip = AudioFileClip(temp_vid_path)
        clip.write_audiofile(temp_audio_path, logger=None)
        clip.close()
        
        # 4. Read the resulting audio bytes
        with open(temp_audio_path, 'rb') as f:
            audio_bytes = f.read()
        
        # 5. Cleanup temporary files from the server
        os.remove(temp_vid_path)
        os.remove(temp_audio_path)
        
        return audio_bytes
    except Exception as e:
        st.error(f"Audio extraction failed: {e}")
        return None

# --- 5. AUTHENTICATION ---
if 'user' not in st.session_state: 
    st.session_state.user = None

if st.session_state.user is None:
    st.title("⚾ League Hub")
    choice = st.radio("Select Action", ["Login", "Join a League", "Create a League"], horizontal=True)

    if choice == "Create a League":
        st.subheader("🛡️ Create New League")
        new_l = st.text_input("League Name").strip().upper()
        new_code = st.text_input("Join Code").strip()
        email = st.text_input("Admin Email")
        pwd = st.text_input("Password", type="password")
        u_name = st.text_input("Full Name")
        
        if st.button("Initialize League"):
            try:
                supabase.auth.sign_up({"email": email, "password": pwd})
                supabase.table('leagues').insert({"name": new_l, "join_code": new_code, "admin_email": email}).execute()
                supabase.table('profiles').update({"username": u_name, "role": "Announcer", "league": new_l}).eq('email', email).execute()
                st.success("League created! Please log in.")
            except Exception as e:
                st.error(f"Setup Error: {e}")

    elif choice == "Join a League":
        st.subheader("🔑 Join Team")
        input_code = st.text_input("Invite Code").strip()
        if st.button("Verify Code"):
            match = supabase.table('leagues').select("name").eq('join_code', input_code).execute()
            if match.data:
                st.session_state.found_league = match.data[0]['name']
                team_q = supabase.table('teams').select("name").eq('league', st.session_state.found_league).execute()
                st.session_state.league_teams = [t['name'] for t in team_q.data]
                st.success(f"Verified for {st.session_state.found_league}")

        if 'found_league' in st.session_state:
            reg_email = st.text_input("Email")
            reg_pwd = st.text_input("Password", type="password")
            reg_name = st.text_input("Your Name")
            reg_role = st.selectbox("Role", ["Player", "Coach"])
            sel_team = st.selectbox("Select Your Team", options=st.session_state.get('league_teams', []))
            
            if st.button("Complete Sign Up"):
                try:
                    supabase.auth.sign_up({"email": reg_email, "password": reg_pwd})
                    supabase.table('profiles').update({
                        "username": reg_name, 
                        "role": reg_role, 
                        "league": st.session_state.found_league, 
                        "team": sel_team
                    }).eq('email', reg_email).execute()
                    st.success("Signup successful! Switch to Login.")
                except Exception as e:
                    st.error(f"Error: {e}")

    else:
        login_email = st.text_input("Email")
        login_pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                auth_res = supabase.auth.sign_in_with_password({"email": login_email, "password": login_pwd})
                p = supabase.table('profiles').select("*").eq('email', login_email).single().execute()
                st.session_state.user = p.data
                st.rerun()
            except:
                st.error("Login failed.")

# --- 6. DASHBOARD ---
else:
    u = st.session_state.user
    l_name = u.get("league", "General")
    my_team = u.get("team", "Unassigned")
    
    st.sidebar.title(f"👤 {u.get('username')}")
    st.sidebar.info(f"Team: {my_team}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    if u.get('role') == "Announcer":
        tabs = st.tabs(["🎙️ Game Deck", "⚙️ Teams", "👤 My Profile"])
        with tabs[1]:
            t_in = st.text_input("New Team Name")
            if st.button("Add Team"):
                supabase.table('teams').insert({"name": t_in, "league": l_name}).execute()
                st.rerun()

    elif u.get('role') == "Coach":
        tabs = st.tabs([f"📋 {my_team} Roster", "👤 My Profile"])
        with tabs[0]:
            st.header(f"Roster: {my_team}")
            players = supabase.table('profiles').select("*").eq('team', my_team).execute()
            for p in players.data:
                st.write(f"#{p.get('player_number', '??')} - {p['username']}")

    else: # Player
        tabs = st.tabs(["💎 My Field", "👤 My Profile"])

    # --- SHARED: UPLOAD LOGIC ---
    with tabs[-1]:
        st.header("Profile Settings")
        col1, col2 = st.columns(2)
        with col1:
            new_num = st.text_input("Jersey #", value=u.get('player_number', ''))
            if st.button("Update Jersey"):
                supabase.table('profiles').update({"player_number": new_num}).eq('email', u['email']).execute()
                st.success("Updated!")
        
        with col2:
            st.subheader("Walk-Up Song")
            # Accepts Video OR Audio
            file = st.file_uploader("Upload Screen Recording or MP3", type=['mp3', 'mp4', 'mov', 'avi'])
            
            if st.button("Save Walk-Up"):
                if file:
                    with st.spinner("Stripping audio from file..."):
                        ext = file.name.split('.')[-1].lower()
                        
                        # If it's a video, strip the audio
                        if ext in ['mp4', 'mov', 'avi']:
                            processed_bytes = extract_audio_from_video(file)
                        else:
                            processed_bytes = file.read()
                        
                        if processed_bytes:
                            # Save to Supabase storage as a standard .mp3
                            path = f"songs/{u['email']}.mp3"
                            url = save_file_to_supabase(processed_bytes, path)
                            supabase.table('profiles').update({"walkup_url": url}).eq('email', u['email']).execute()
                            st.success("Walk-up song uploaded and converted!")
