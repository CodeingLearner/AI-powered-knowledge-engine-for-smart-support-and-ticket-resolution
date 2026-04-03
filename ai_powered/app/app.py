import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import pandas as pd
import time
from datetime import datetime

# Import backend modules
import auth_service
import ticket_service
import config

# Page configuration
st.set_page_config(
    page_title="AI Support System",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stTextInput, .stTextArea, .stSelectbox {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #2563eb;
    }
    .ticket-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #3b82f6;
    }
    .resolution-resolved {
        border-left-color: #10b981;
    }
    .resolution-tentative {
        border-left-color: #f59e0b;
    }
    .resolution-unresolved {
        border-left-color: #ef4444;
    }
    .confidence-high {
        color: #10b981;
        font-weight: bold;
    }
    .confidence-medium {
        color: #f59e0b;
        font-weight: bold;
    }
    .confidence-low {
        color: #ef4444;
        font-weight: bold;
    }
    .tab-content {
        padding: 20px;
        background-color: #1e1e1e;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def get_confidence_class(confidence):
    """Get CSS class based on confidence score."""
    if confidence >= 0.8:
        return "confidence-high"
    elif confidence >= 0.6:
        return "confidence-medium"
    else:
        return "confidence-low"

def get_resolution_class(status):
    """Get CSS class based on resolution status."""
    if status == "resolved":
        return "resolution-resolved"
    elif status == "tentative":
        return "resolution-tentative"
    else:
        return "resolution-unresolved"

def login_page():
    """Display login/signup page."""
    st.title("🔧 AI-Powered Support System")
    st.markdown("---")

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

    with tab1:
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

    with tab2:
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

def new_incident_tab():
    """Display new incident submission form."""
    st.header("🚨 Submit New Incident")

    with st.form("ticket_form"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Issue Title", placeholder="Brief description of the problem")
            category = st.selectbox(
                "Category",
                ["Technical", "Billing", "Account", "General", "Other"],
                key="category"
            )

        with col2:
            priority = st.selectbox(
                "Priority",
                ["Low", "Medium", "High", "Critical"],
                key="priority"
            )

        description = st.text_area(
            "Detailed Description",
            placeholder="Please provide as much detail as possible about the issue...",
            height=150
        )

        submit_button = st.form_submit_button("🚀 Submit Ticket", use_container_width=True)

        if submit_button:
            if not title or not description:
                st.error("Please fill in title and description.")
            else:
                with st.spinner("Analyzing ticket with AI..."):
                    try:
                        ticket = ticket_service.submit_ticket(
                            title=title,
                            description=description,
                            category=category,
                            priority=priority,
                            user_id=st.session_state.user['username']
                        )

                        st.success("✅ Ticket submitted successfully!")

                        # Display AI resolution
                        st.markdown("### 🤖 AI Resolution")
                        confidence_class = get_confidence_class(ticket['confidence_score'])

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Confidence Score", f"{ticket['confidence_score']:.1%}")
                        with col2:
                            st.metric("Status", ticket['resolution_status'].title())
                        with col3:
                            st.metric("Knowledge Found", "Yes" if ticket['kb_context_found'] else "No")

                        # Resolution text
                        st.markdown("**Resolution:**")
                        st.info(ticket['ai_resolution'])

                        # Additional details
                        with st.expander("📊 Analysis Details"):
                            st.write(f"**Retrieval Score:** {ticket['retrieval_score']:.3f}")
                            if ticket.get('suggested_kb_filename'):
                                st.write(f"**Suggested Knowledge File:** {ticket['suggested_kb_filename']}")

                    except Exception as e:
                        st.error(f"Error submitting ticket: {str(e)}")

def ticket_history_tab():
    """Display user's ticket history."""
    st.header("📂 My Ticket History")

    try:
        tickets_df = ticket_service.get_user_tickets(st.session_state.user['username'])

        if tickets_df.empty:
            st.info("No tickets found. Submit your first incident above!")
        else:
            st.markdown(f"**Total Tickets:** {len(tickets_df)}")

            # Filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                status_filter = st.multiselect(
                    "Filter by Status",
                    options=["resolved", "tentative", "unresolved"],
                    default=["resolved", "tentative", "unresolved"],
                    key="status_filter"
                )
            with col2:
                category_filter = st.multiselect(
                    "Filter by Category",
                    options=tickets_df['category'].unique().tolist(),
                    default=tickets_df['category'].unique().tolist(),
                    key="category_filter"
                )
            with col3:
                priority_filter = st.multiselect(
                    "Filter by Priority",
                    options=tickets_df['priority'].unique().tolist(),
                    default=tickets_df['priority'].unique().tolist(),
                    key="priority_filter"
                )

            # Apply filters
            filtered_df = tickets_df[
                (tickets_df['resolution_status'].isin(status_filter)) &
                (tickets_df['category'].isin(category_filter)) &
                (tickets_df['priority'].isin(priority_filter))
            ]

            # Display tickets
            for _, ticket in filtered_df.iterrows():
                resolution_class = get_resolution_class(ticket['resolution_status'])
                confidence_class = get_confidence_class(ticket['confidence_score'])

                with st.container():
                    st.markdown(f"""
                    <div class="ticket-card {resolution_class}">
                        <h4>#{ticket['id']} - {ticket['title']}</h4>
                        <p><strong>Category:</strong> {ticket['category']} |
                        <strong>Priority:</strong> {ticket['priority']} |
                        <strong>Status:</strong> <span class="{confidence_class}">{ticket['resolution_status'].title()}</span></p>
                        <p><strong>Confidence:</strong> <span class="{confidence_class}">{ticket['confidence_score']:.1%}</span> |
                        <strong>Created:</strong> {ticket['created_at']}</p>
                        <details>
                            <summary>📋 Description</summary>
                            <p>{ticket['description']}</p>
                        </details>
                        <details>
                            <summary>🤖 AI Resolution</summary>
                            <p>{ticket['ai_resolution']}</p>
                        </details>
                    </div>
                    """, unsafe_allow_html=True)

                # Feedback section
                if pd.isna(ticket.get('feedback_value')):
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"👍 Helpful", key=f"helpful_{ticket['id']}"):
                            ticket_service.submit_feedback(ticket['id'], "helpful", st.session_state.user['username'])
                            st.success("Thank you for your feedback!")
                            time.sleep(1)
                            st.rerun()
                    with col2:
                        if st.button(f"👎 Not Helpful", key=f"not_helpful_{ticket['id']}"):
                            ticket_service.submit_feedback(ticket['id'], "not_helpful", st.session_state.user['username'])
                            st.success("Thank you for your feedback!")
                            time.sleep(1)
                            st.rerun()
                else:
                    st.caption(f"Feedback: {'👍 Helpful' if ticket['feedback_value'] == 'helpful' else '👎 Not Helpful'}")

                st.markdown("---")

    except Exception as e:
        st.error(f"Error loading ticket history: {str(e)}")

def main_app():
    """Main application after login."""
    # Header with logout
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.write(f"👤 **{st.session_state.user['username']}**")
    with col2:
        st.title("🔧 AI Support Dashboard")
    with col3:
        if st.button("🚪 Logout", key="logout"):
            del st.session_state.user
            st.session_state.page = "login"
            st.rerun()

    st.markdown("---")

    # Main tabs
    tab1, tab2 = st.tabs(["🚨 New Incident", "📂 My History"])

    with tab1:
        new_incident_tab()

    with tab2:
        ticket_history_tab()

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