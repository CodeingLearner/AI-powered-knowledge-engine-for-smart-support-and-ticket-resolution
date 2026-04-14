import sys
import os
import base64

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import time

# Import backend modules
import auth_service
import ticket_service

# Import our new view modules
from views.styles import inject_custom_css
from views.user_dashboard import render_user_dashboard
from views.admin_dashboard import render_admin_dashboard

# Page configuration MUST be the first Streamlit command
st.set_page_config(
    page_title="AI Support System",
    page_icon="logo.png",
    layout="centered",
    initial_sidebar_state="expanded"
)


# Inject our global CSS design tokens
inject_custom_css()

def login_page():
    """Display login/signup page."""
    # Center logo and title flawlessly using an HTML Flexbox
    try:
        with open(r"D:\SPRINGBORD_PROJECT\updated\AI-powered\ai_powered\logo.png", "rb") as img_file:
            img_b64 = base64.b64encode(img_file.read()).decode()
            
        st.markdown(f"""
            <div style="display: flex; justify-content: center; align-items: center; margin-top: 20px; margin-bottom: 20px;">
                <img src="data:image/png;base64,{img_b64}" width="80" style="margin-right: 20px;" />
                <h1 style="margin: 0; padding: 0; line-height: 1; white-space: nowrap;">AI Support System</h1>
            </div>
            """, unsafe_allow_html=True)
    except FileNotFoundError:
        st.title("🔧 AI Support System")
    st.markdown("---")

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            login_button = st.form_submit_button("Login", use_container_width=True)

            if login_button:
                if not username or not password:
                    st.error("Please fill in all fields.")
                else:
                    user = auth_service.login_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.page = "main"
                        st.success(f"Welcome back, {user['username']}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Create New Account")
        with st.form("signup_form"):
            new_username = st.text_input("Username", key="signup_username")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            signup_button = st.form_submit_button("Sign Up", use_container_width=True)

            if signup_button:
                if not new_username or not new_password:
                    st.error("Please fill in all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long.")
                else:
                    if auth_service.register_user(new_username, new_password):
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error("Username already exists.")
        st.markdown('</div>', unsafe_allow_html=True)

def main_app():
    """Main application routing based on role."""
    # Top Level App Bar
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.markdown(f"👤 **{st.session_state.user['username']}**", unsafe_allow_html=True)
    with col2:
        # Re-use our robust HTML Flexbox header for a consistent SaaS design
        try:
            with open(r"D:\SPRINGBORD_PROJECT\updated\AI-powered\ai_powered\logo.png", "rb") as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode()
            st.markdown(f"""
                <div style="display: flex; justify-content: center; align-items: center;">
                    <img src="data:image/png;base64,{img_b64}" width="45" style="margin-right: 15px;" />
                    <h2 style="margin: 0; padding: 0; line-height: 1; white-space: nowrap;">AI Support Dashboard</h2>
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            st.markdown("<h2 style='text-align: center; white-space: nowrap;'>🔧 AI Support Dashboard</h2>", unsafe_allow_html=True)
    with col3:
        if st.button("🚪 Logout", key="logout", use_container_width=True):
            del st.session_state.user
            st.session_state.page = "login"
            st.rerun()

    st.markdown("---")

    # Role-based Routing
    role = st.session_state.user.get('role', 'user')
    if role == 'admin':
        render_admin_dashboard()
    else:
        render_user_dashboard()

def main():
    """Main application entry point."""
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    if 'user' not in st.session_state:
        st.session_state.user = None

    # Initialize system on first run
    if 'system_initialized' not in st.session_state:
        with st.spinner("Initializing system..."):
            ticket_service.initialize_system()
        st.session_state.system_initialized = True

    # Route to appropriate page
    if st.session_state.page == "login" or st.session_state.user is None:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()