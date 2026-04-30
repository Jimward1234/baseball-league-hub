import streamlit as st
from supabase import create_client, Client

# --- DATABASE CONNECTION ---
# These are copied exactly from your credentials image
URL = "https://cdjjtomuokuluhvsjxpd.supabase.co"
# I've verified this string against your image_c5e0fe.png
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNkamp0b211b2t1bHVodnNqeHBkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0OTc3NzMsImV4cCI6MjA5MzA3Mzc3M30.oNrH9jmeyXxedj0NTRrhTilpGtOoPRZzy6SA5rsy16g"

try:
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error(f"Failed to connect to Supabase: {e}")

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
                    p = supabase.table('profiles').select("*").eq('email', l_email).execute()
                    if p.data:
                        st.session_state.user = p.data[0]
                        st.success(f"Welcome back!")
                        st.rerun()
                    else:
                        st.error("Account found, but no profile data exists. Try 'Join'.")
            except Exception as e:
                st.error("Login failed. Check your email/password or confirm the user in Supabase.")

    elif choice == "Join":
        st.subheader("🔑 Join the League")
        reg_email = st.text_input("Email").strip().lower()
        reg_pwd = st.text_input("Password", type="password")
        reg_name = st.text_input("Full Name")
        reg_role = st.selectbox("Role", ["Player", "Coach"])
        sel_team = st.selectbox("Select Team", ["storm", "other"])

        if st.button("Complete Sign Up"):
            try:
                # This creates the user in the 'Authentication' tab automatically
                auth_res = supabase.auth.sign_up({"email": reg_email, "password": reg_pwd})
                
                if auth_res.user:
                    # This links them to your 60-person roster automatically
                    supabase.table('profiles').update({
                        "id": auth_res.user.id, 
                        "role": reg_role, 
                        "team": sel_team,
                        "username": reg_name
                    }).eq('email', reg_email).execute()
                    
                    st.success("✅ Success! Now switch to the 'Login' tab.")
            except Exception as e:
                st.error(f"Sign up failed: {e}")

# --- MAIN APP ---
else:
    if st.sidebar.button("Logout"):
        supabase.auth.sign_out()
        del st.session_state.user
        st.rerun()
    
    u = st.session_state.user
    st.write(f"Logged in as: {u['username']} ({u['role']})")
