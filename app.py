import streamlit as st
from supabase import create_client, Client

# --- SETUP ---
url = st.secrets["https://cdjjtomuokuluhvsjxpd.supabase.co"]
key = st.secrets["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNkamp0b211b2t1bHVodnNqeHBkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzQ5Nzc3MywiZXhwIjoyMDkzMDczNzczfQ.waRifcTydbUakJIO7fHimlHT1Y8ifipi-gP6FIXlaFY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="League Hub", page_icon="⚾")

# --- AUTH LOGIC ---
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
                        st.success(f"Welcome back, {st.session_state.user['username']}!")
                        st.rerun()
                    else:
                        st.error("Auth successful, but no profile found in database.")
            except Exception:
                st.error("Login failed. Check your credentials.")

    elif choice == "Join":
        st.subheader("🔑 Join Existing League")
        reg_email = st.text_input("Email").strip().lower()
        reg_pwd = st.text_input("Password", type="password")
        reg_name = st.text_input("Full Name")
        reg_role = st.selectbox("Role", ["Player", "Coach"])
        
        # Hardcoding 'storm' for your current setup, or use your league logic
        sel_team = st.selectbox("Select Team", ["storm", "other"])

        if st.button("Complete Sign Up"):
            try:
                # 1. Create the Auth Account
                auth_res = supabase.auth.sign_up({"email": reg_email, "password": reg_pwd})
                
                if auth_res.user:
                    new_uid = auth_res.user.id
                    # 2. AUTO-SYNC: Update the existing row for your 60 users
                    supabase.table('profiles').update({
                        "id": new_uid, 
                        "role": reg_role, 
                        "team": sel_team,
                        "username": reg_name
                    }).eq('email', reg_email).execute()
                    
                    st.success("✅ Success! Switch to 'Login' tab to enter the app.")
            except Exception as e:
                if "already registered" in str(e).lower():
                    st.info("You're already signed up! Just go to the 'Login' tab.")
                else:
                    st.error(f"Error: {e}")

# --- APP LOGIC (COACH DASHBOARD) ---
else:
    u = st.session_state.user
    my_team = u.get('team', 'DEMO')

    if u.get('role') == "Coach":
        tabs = st.tabs([f"📋 {my_team} Management", "👤 Profile"])
        with tabs[0]:
            players_q = supabase.table('profiles').select("*").eq('team', my_team).execute()
            roster = players_q.data
            col_list, col_field = st.columns([1, 2])
            
            with col_list:
                st.subheader("Assign Positions")
                for p in roster:
                    current_pos = p.get('position', 'Sub')
                    pos_options = ["Sub", "P", "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]
                    
                    # Logic to find the current position index
                    try:
                        idx = pos_options.index(current_pos)
                    except ValueError:
                        idx = 0
                    
                    new_pos = st.selectbox(f"{p['username']}", pos_options, index=idx, key=f"pos_{p['email']}")
                    
                    if new_pos != current_pos:
                        try:
                            # Safety wrapper for the update
                            supabase.table('profiles').update({"position": new_pos}).eq('email', p['email']).execute()
                            st.rerun()
                        except Exception:
                            st.warning("⚠️ Database Update Failed: Check your RLS Policies.")
            
            with col_field:
                # Assuming your draw_diamond function is defined elsewhere in your file
                if 'draw_diamond' in globals():
                    draw_diamond(roster)
                else:
                    st.info("Diamond view will appear here.")

    if st.sidebar.button("Logout"):
        supabase.auth.sign_out()
        del st.session_state.user
        st.rerun()
