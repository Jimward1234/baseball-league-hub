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
    import moviepy.editor as mp
    from moviepy.editor import AudioFileClip
except ImportError:
    st.error("⚠️ MoviePy not found. Please Reboot the app in Streamlit Cloud.")

# --- 3. THEME & STYLING ---
st.set_page_config(page_title="League Hub", layout="wide")

st.markdown("""
    <style>
    .stAudio { width: 100% !important; }
    audio { height: 45px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; color: white; background-color: #ff4b4b; }
    .main-header { font-size: 2.5rem; font-weight: bold; margin-bottom: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS ---
def save_file_to_supabase(file_bytes, path):
    """Uploads file bytes to Supabase Storage."""
    try:
        supabase.storage.from_('uploads').upload(path, file_bytes, {"upsert": "true"})
        return supabase.storage.from_('uploads').get_public_url(path)
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None

def extract_audio_from_video(video_file):
    """Strips audio from mp4/mov and returns MP3 bytes."""
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

# --- 5. AUTHENTICATION ---
if 'user' not in st.session_state: 
    st.session_state.user = None

if st.session_state.user is None:
    st.title("⚾ League Hub")
    choice = st.radio("Select Action", ["Login", "Join a League", "Create a League"], horizontal=True)

    if choice == "Create a League":
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
            except Exception as e:
                st.error(f"Setup Error: {e}")

    elif choice == "Join a League":
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
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.subheader("👋 Welcome Back")
        l_email = st.text_input("Email")
        l_pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                supabase.auth.sign_in_with_password({"email": l_email, "password": l_pwd})
                p = supabase.table('profiles').select("*").eq('email', l_email).single().execute()
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
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    if u.get('role') == "Announcer":
        tabs = st.tabs(["🎙️ Game Deck", "⚙️ Manage", "👤 Profile"])
        # (Announcer logic remains same as previous steps)
    elif u.get('role') == "Coach":
        tabs = st.tabs([f"📋 {my_team}", "👤 Profile"])
        # (Coach logic remains same as previous steps)
    else:
        tabs = st.tabs(["💎 My Field", "👤 Profile"])

    with tabs[-1]:
        st.header("My Profile Settings")
        col1, col2 = st.columns(2)
        with col1:
            new_num = st.text_input("Jersey Number", value=u.get('player_number', ''))
            if st.button("Update Jersey"):
                supabase.table('profiles').update({"player_number": new_num}).eq('email', u['email']).execute()
                st.success("Jersey updated!")
        
        with col2:
            st.subheader("Walk-Up Song")
            media = st.file_uploader("Upload Video or MP3", type=['mp3', 'mp4', 'mov', 'avi'])
            if st.button("Save Walk-Up"):
                if media:
                    with st.spinner("Processing..."):
                        ext = media.name.split('.')[-1].lower()
                        # Variable sync fix applied here
                        if ext in ['mp4', 'mov', 'avi']:
                            audio_data = extract_audio_from_video(media)
                        else:
                            audio_data = media.read()
                        
                        if audio_data:
                            file_path = f"songs/{u['email']}.mp3"
                            url = save_file_to_supabase(audio_data, file_path)
                            if url:
                                supabase.table('profiles').update({"walkup_url": url}).eq('email', u['email']).execute()
                                st.success("Walk-up song processed and saved!")
