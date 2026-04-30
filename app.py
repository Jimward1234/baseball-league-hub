import streamlit as st
from supabase import create_client, Client

# --- DATABASE CONNECTION ---
# Verified from your image_c5e0fe.png
URL = "https://cdjjtomuokuluhvsjxpd.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc2MiOiJzdXByYWJhc2UiLCJuYW1lIj0b211b2t1bHVzanhwZCIsImV4cCI6ImFub24iLCJpYXQiOjE3Nzc0Tc3NzMsImV4cCI6MjA5MzA3Mzc3M30.oNrH9jmeyXkedj0NTRrhTilpGt0oPRZZy6SA5rsy16g"

supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="League Hub", page_icon="⚾")

if 'user' not in st.session_state:
    st.title("⚾ League Hub")
    choice = st.radio("Action", ["Login", "Join"], horizontal=True)

    if choice == "Login":
        l_email = st.text_input("Email").strip().lower()
        l_pwd = st.text_input("Password", type="password")
        
        if st.button("Login"):
            try:
                # 1. Log into the authentication gate
                res = supabase.auth.sign_in_with_password({"email": l_email, "password": l_pwd})
                if res.user:
                    # 2. Grab the user's data from the profiles table
                    p = supabase.table('profiles').select("*").eq('id', res.user.id).execute()
                    
                    if p.data:
                        st.session_state.user = p.data[0]
                        st.rerun()
                    else:
                        # AUTO-FIX: Create a profile if one is missing
                        new_data = {"id": res.user.id, "email": l_email, "role": "Coach", "username": "Coach Admin"}
                        supabase.table('profiles').upsert(new_data).execute()
                        st.session_state.user = new_data
                        st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

    elif choice == "Join":
        st.subheader("🔑 Join the League")
        reg_email = st.text_input("Email").strip().lower()
        reg_pwd = st.text_input("Password", type="password")
        reg_name = st.text_input("Full Name")
        reg_role = st.selectbox("Role", ["Player", "Coach"])

        if st.button("Complete Sign Up"):
            try:
                # Create the user in Authentication
                auth_res = supabase.auth.sign_up({"email": reg_email, "password": reg_pwd})
                if auth_res.user:
                    # Link to the roster automatically
                    profile_data = {
                        "id": auth_res.user.id, 
                        "email": reg_email,
                        "role": reg_role, 
                        "username": reg_name
                    }
                    # Upsert finds existing email and adds the ID
                    supabase.table('profiles').upsert(profile_data, on_conflict="email").execute()
                    st.success("✅ Success! Now go to the 'Login' tab.")
            except Exception as e:
                st.error(f"Sign up error: {e}")

else:
    u = st.session_state.user
    st.title(f"⚾ Welcome, {u.get('username', 'User')}!")
    
    if st.sidebar.button("Logout"):
        supabase.auth.sign_out()
        del st.session_state.user
        st.rerun()

    if u.get('role') == "Coach":
        st.subheader("📋 Team Roster")
        roster = supabase.table('profiles').select("*").execute()
        if roster.data:
            st.dataframe(roster.data)
