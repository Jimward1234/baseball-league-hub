import streamlit as st
from supabase import create_client, Client

# --- THE ENGINE ROOM ---
URL = "https://cdjjtomuokuluhvsjxpd.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc2MiOiJzdXByYWJhc2UiLCJuYW1lIj0b211b2t1bHVzanhwZCIsImV4cCI6ImFub24iLCJpYXQiOjE3Nzc0Tc3NzMsImV4cCI6MjA5MzA3Mzc3M30.oNrH9jmeyXkedj0NTRrhTilpGt0oPRZZy6SA5rsy16g"

try:
    supabase: Client = create_client(URL, KEY)
    # Silent check to see if the API key is actually working
    supabase.table('profiles').select("count", count="exact").limit(1).execute()
    connection_status = True
except Exception:
    connection_status = False

st.set_page_config(page_title="League Hub", layout="wide")

# --- LOGIN BARRIER ---
if 'user' not in st.session_state:
    if not connection_status:
        st.error("⚠️ The app cannot talk to your database. Please check your Supabase 'Anon' key.")
        st.stop()

    st.title("⚾ League Hub")
    tab1, tab2 = st.tabs(["Login", "Join League"])

    with tab1:
        email = st.text_input("Email").lower().strip()
        pw = st.text_input("Password", type="password")
        if st.button("Log In"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                p = supabase.table('profiles').select("*").eq('id', res.user.id).execute()
                if p.data:
                    st.session_state.user = p.data[0]
                    st.rerun()
            except Exception as e:
                st.error(f"Login Failed: {e}")

    with tab2:
        st.info("New here? Enter your details to link your roster spot.")
        r_email = st.text_input("Register Email").lower().strip()
        r_pw = st.text_input("Create Password", type="password")
        r_name = st.text_input("Full Name")
        r_role = st.selectbox("Your Role", ["Player", "Coach", "Announcer"])
        
        if st.button("Create Account"):
            try:
                auth = supabase.auth.sign_up({"email": r_email, "password": r_pw})
                if auth.user:
                    # This connects the login to your 60-person list automatically
                    supabase.table('profiles').upsert({
                        "id": auth.user.id, "email": r_email, "username": r_name, "role": r_role
                    }, on_conflict="email").execute()
                    st.success("✅ Success! You can now log in.")
            except Exception as e:
                st.error(f"Sign up failed: {e}")

# --- THE ACTUAL APP ---
else:
    u = st.session_state.user
    st.sidebar.title(f"Hi, {u['username']}!")
    
    if u['role'] == "Coach":
        st.header("📋 Coach's Command Center")
        # I can add the roster management and diamond view here next!
        
    elif u['role'] == "Player":
        st.header("🎵 Player Dashboard")
        st.write("Upload your walk-up song here.")
        # I can add the .mp4 to .mp3 converter here next!

    if st.sidebar.button("Log Out"):
        supabase.auth.sign_out()
        del st.session_state.user
        st.rerun()
