import streamlit as st
from supabase import create_client, Client

# --- DATABASE CONNECTION ---
# Hardcoded with your specific credentials from image_c5e0fe.png
URL = "https://cdjjtomuokuluhvsjxpd.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc2MiOiJzdXByYWJhc2UiLCJuYW1lIj0b211b2t1bHVzanhwZCIsImV4cCI6ImFub24iLCJpYXQiOjE3Nzc0Tc3NzMsImV4cCI6MjA5MzA3Mzc3M30.oNrH9jmeyXkedj0NTRrhTilpGt0oPRZZy6SA5rsy16g"

supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="League Hub", page_icon="⚾")

# --- AUTHENTICATION LOGIC ---
if 'user' not in st.session_state:
    st.title("⚾ League Hub")
    choice = st.radio("Action", ["Login", "Join", "Create", "Forgot Password"], horizontal=True)

    if choice == "Login":
        l_email = st.text_input("Email").strip().lower()
        l_pwd = st.text_input("Password", type="password")
        
        if st.button("Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": l_email, "password": l_pwd})
                if res.user:
                    # Look up user in the 60-person roster
                    p = supabase.table('profiles').select("*").eq('email', l_email).execute()
                    if p.data:
                        st.session_state.user = p.data[0]
                        st.success(f"Welcome back, {st.session_state.user['username']}!")
                        st.rerun()
                    else:
                        st.error("Profile not found. Please 'Join' to link your account.")
            except Exception:
                st.error("Login failed. Check your credentials.")

    elif choice == "Join":
        st.subheader("🔑 Join the League")
        reg_email = st.text_input("Email").strip().lower()
        reg_pwd = st.text_input("Password", type="password")
        reg_name = st.text_input("Full Name")
        reg_role = st.selectbox("Role", ["Player", "Coach"])
        sel_team = st.selectbox("Select Team", ["storm", "other"])

        if st.button("Complete Sign Up"):
            try:
                # 1. Create the Auth Account
                auth_res = supabase.auth.sign_up({"email": reg_email, "password": reg_pwd})
                
                if auth_res.user:
                    new_uid = auth_res.user.id
                    # 2. AUTOMATIC SYNC: Links new login to existing 60-user roster
                    supabase.table('profiles').update({
                        "id": new_uid, 
                        "role": reg_role, 
                        "team": sel_team,
                        "username": reg_name
                    }).eq('email', reg_email).execute()
                    
                    st.success("✅ Success! Now switch to the 'Login' tab.")
            except Exception as e:
                if "already registered" in str(e).lower():
                    st.info("You're already signed up! Switch to 'Login'.")
                else:
                    st.error(f"Error: {e}")

# --- MAIN APP LOGIC ---
else:
    u = st.session_state.user
    my_team = u.get('team', 'DEMO')

    # COACH DASHBOARD
    if u.get('role') == "Coach":
        st.title(f"📋 {my_team} Management")
        players_q = supabase.table('profiles').select("*").eq('team', my_team).execute()
        roster = players_q.data
        
        st.subheader("Assign Positions")
        for p in roster:
            current_pos = p.get('position', 'Sub')
            pos_options = ["Sub", "P", "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]
            
            try:
                idx = pos_options.index(current_pos)
            except ValueError:
                idx = 0
            
            new_pos = st.selectbox(f"Position for {p['username']}", pos_options, index=idx, key=f"pos_{p['email']}")
            
            if new_pos != current_pos:
                try:
                    # Safety fix to prevent crashes
                    supabase.table('profiles').update({"position": new_pos}).eq('email', p['email']).execute()
                    st.rerun()
                except Exception:
                    st.warning("⚠️ Update failed. Ensure RLS is enabled in Supabase.")

    # LOGOUT
    if st.sidebar.button("Logout"):
        supabase.auth.sign_out()
        del st.session_state.user
        st.rerun()
