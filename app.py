import streamlit as st
from supabase import create_client, Client

# --- DATABASE CONNECTION ---
URL = "https://cdjjtomuokuluhvsjxpd.supabase.co"
# TRIPLE-CHECK: Ensure no spaces are at the end of this string!
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc2MiOiJzdXByYWJhc2UiLCJuYW1lIj0b211b2t1bHVzanhwZCIsImV4cCI6ImFub24iLCJpYXQiOjE3Nzc0Tc3NzMsImV4cCI6MjA5MzA3Mzc3M30.oNrH9jmeyXkedj0NTRrhTilpGt0oPRZZy6SA5rsy16g"

try:
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error(f"❌ Connection Error: {e}")

st.set_page_config(page_title="League Hub", page_icon="⚾")

if 'user' not in st.session_state:
    st.title("⚾ League Hub")
    choice = st.radio("Action", ["Login", "Join"], horizontal=True)

    if choice == "Join":
        st.subheader("🔑 Join the League")
        reg_email = st.text_input("Email").strip().lower()
        reg_pwd = st.text_input("Password", type="password")
        reg_name = st.text_input("Full Name")
        reg_role = st.selectbox("Role", ["Player", "Coach"])

        if st.button("Complete Sign Up"):
            if not reg_email or not reg_pwd:
                st.warning("Please fill in email and password.")
            else:
                try:
                    # SIGN UP STEP
                    auth_res = supabase.auth.sign_up({"email": reg_email, "password": reg_pwd})
                    
                    if auth_res.user:
                        # LINK TO ROSTER STEP
                        profile_data = {
                            "id": auth_res.user.id, 
                            "email": reg_email,
                            "role": reg_role, 
                            "username": reg_name,
                            "team": "storm"
                        }
                        # Using upsert to handle pre-existing roster rows
                        supabase.table('profiles').upsert(profile_data, on_conflict="email").execute()
                        st.success("✅ Account Created! Now switch to 'Login'.")
                    else:
                        st.error("User created but no ID returned. Check Supabase Auth settings.")
                        
                except Exception as e:
                    # THIS IS THE KEY: It will show us the exact API error code
                    st.error(f"⚠️ Sign up failed: {e}")
                    if "apiKey" in str(e) or "401" in str(e):
                        st.info("💡 Tip: Your API key is being rejected. Go to Supabase > Settings > API and copy the 'anon public' key again.")

    elif choice == "Login":
        # ... (Your existing Login code) ...
        l_email = st.text_input("Email").strip().lower()
        l_pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": l_email, "password": l_pwd})
                if res.user:
                    p = supabase.table('profiles').select("*").eq('id', res.user.id).execute()
                    if p.data:
                        st.session_state.user = p.data[0]
                        st.rerun()
            except Exception as e:
                st.error(f"Login Error: {e}")

else:
    st.write(f"Logged in as {st.session_state.user['username']}")
    if st.sidebar.button("Logout"):
        del st.session_state.user
        st.rerun()
