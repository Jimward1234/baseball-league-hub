import streamlit as st
from supabase import create_client, Client

# --- DATABASE CONNECTION ---
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
                res = supabase.auth.sign_in_with_password({"email": l_email, "password": l_pwd})
                if res.user:
                    # Search for the user in your 60-person roster
                    p = supabase.table('profiles').select("*").eq('email', l_email).execute()
                    if p.data:
                        st.session_state.user = p.data[0]
                        st.rerun()
                    else:
                        # EMERGENCY FIX: If Auth exists but profile is missing, create a basic one
                        new_profile = {
                            "id": res.user.id,
                            "email": l_email,
                            "username": l_email.split('@')[0],
                            "role": "Coach" # Defaulting to coach for your test
                        }
                        supabase.table('profiles').insert(new_profile).execute()
                        st.session_state.user = new_profile
                        st.rerun()
            except Exception:
                st.error("Login failed. Check your credentials.")

    elif choice == "Join":
        st.subheader("🔑 Join the League")
        reg_email = st.text_input("Email").strip().lower()
        reg_pwd = st.text_input("Password", type="password")
        reg_name = st.text_input("Full Name")
        reg_role = st.selectbox("Role", ["Player", "Coach"])

        if st.button("Complete Sign Up"):
            try:
                auth_res = supabase.auth.sign_up({"email": reg_email, "password": reg_pwd})
                if auth_res.user:
                    # This is the "Automatic Sync" for your 60 users
                    # It tries to find their existing email and update it with their new ID
                    check = supabase.table('profiles').select("*").eq('email', reg_email).execute()
                    
                    data = {
                        "id": auth_res.user.id, 
                        "role": reg_role, 
                        "username": reg_name
                    }
                    
                    if check.data:
                        supabase.table('profiles').update(data).eq('email', reg_email).execute()
                    else:
                        data["email"] = reg_email
                        supabase.table('profiles').insert(data).execute()
                    
                    st.success("✅ Account Linked! Switch to 'Login'.")
            except Exception as e:
                st.error(f"Sign up failed: {e}")

else:
    # --- DASHBOARD AREA ---
    u = st.session_state.user
    st.title(f"Welcome, {u.get('username', 'Coach')}")
    
    if st.sidebar.button("Logout"):
        supabase.auth.sign_out()
        del st.session_state.user
        st.rerun()

    # COACH TOOLS
    if u.get('role') == "Coach":
        st.subheader("📋 Team Management")
        # Restoring your roster view
        res = supabase.table('profiles').select("*").execute()
        if res.data:
            st.write("Current Roster:")
            st.dataframe(res.data)
