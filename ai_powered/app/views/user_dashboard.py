import os
import streamlit as st
import pandas as pd
import time
import shutil


import ticket_service
from .components import render_ticket_card, get_confidence_class
import rag_engine
import auth_service

def render_new_incident():
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
                with st.spinner("Analyzing and retrieving knowledge..."):
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
                        st.markdown("### 🤖 AI Response")
                        confidence_class = get_confidence_class(ticket['confidence_score'])

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Confidence", f"{ticket['confidence_score']:.1%}")
                        with col2:
                            st.metric("Status", ticket['resolution_status'].title())
                        with col3:
                            st.metric("Source Found", "Yes" if ticket['kb_context_found'] else "No")

                        if ticket.get('kb_context_found') and ticket.get('suggested_kb_filename'):
                            st.info(f"📚 Retrieved from knowledge base: **{ticket['suggested_kb_filename']}**")

                        st.markdown("**Resolution:**")
                        st.info(ticket['ai_resolution'])


                    except Exception as e:
                        st.error(f"Error submitting ticket: {str(e)}")


def render_my_tickets():
    """Display user's ticket history."""
    st.header("📂 My Tickets")

    try:
        tickets_df = ticket_service.get_user_tickets(st.session_state.user['username'])

        if tickets_df.empty:
            st.info("No tickets found. Submit your first incident above!")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                status_filter = st.multiselect(
                    "Filter by Status",
                    options=["resolved", "tentative", "unresolved"],
                    default=["resolved", "tentative", "unresolved"],
                    key="status_filter_user"
                )
            with col2:
                category_filter = st.multiselect(
                    "Filter by Category",
                    options=tickets_df['category'].unique().tolist(),
                    default=tickets_df['category'].unique().tolist(),
                    key="category_filter_user"
                )
            with col3:
                priority_filter = st.multiselect(
                    "Filter by Priority",
                    options=tickets_df['priority'].unique().tolist(),
                    default=tickets_df['priority'].unique().tolist(),
                    key="priority_filter_user"
                )

            filtered_df = tickets_df[
                (tickets_df['resolution_status'].isin(status_filter)) &
                (tickets_df['category'].isin(category_filter)) &
                (tickets_df['priority'].isin(priority_filter))
            ]

            for _, ticket in filtered_df.iterrows():
                render_ticket_card(ticket_service, ticket, st.session_state.user['username'])

    except Exception as e:
        st.error(f"Error loading ticket history: {str(e)}")


def handle_document_upload():
    uploaded_files = st.file_uploader("Drag & Drop PDF upload", type=["pdf", "md", "txt"], accept_multiple_files=True)
    if st.button("Upload to Knowledge Base"):
        if uploaded_files:
            os.makedirs(rag_engine.DATA_RAW_DIR, exist_ok=True)
            for uploaded_file in uploaded_files:
                file_path = os.path.join(rag_engine.DATA_RAW_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Uploaded: {uploaded_file.name}")
            
            with st.spinner("Processing documents..."):
                try:
                    rag_engine.ingest_documents()
                    st.success("Documents successfully processed and indexed!")
                except Exception as e:
                    st.error(f"Error during ingestion: {str(e)}")
        else:
            st.warning("Please select files to upload.")

def render_knowledge_base_expander():
    with st.expander("➕ Add Document"):
        st.write("Upload relevant files to help the AI resolve tickets automatically.")
        handle_document_upload()

def render_user_dashboard():
    if 'user_view' not in st.session_state:
        st.session_state.user_view = 'new'

    st.markdown("""
        <style>
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            padding: 0px !important;
            transition: all 0.2s ease;
            overflow: hidden;
            margin-bottom: 6px;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:hover {
            background-color: rgba(255, 255, 255, 0.1);
            border-color: #00b4d8 !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"] {
            gap: 0 !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"] {
            padding: 0 !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] div.stButton > button {
            background: transparent !important;
            border: none !important;
            padding: 8px 4px !important;
            box-shadow: none !important;
            min-height: 0;
            line-height: normal;
            border-radius: 0;
            width: 100%;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] div.stButton > button:hover {
            color: #00b4d8 !important;
            background: rgba(0, 180, 216, 0.15) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("📂 Menu")
        if st.button("📝 Raise new ticket", use_container_width=True, type="primary"):
            st.session_state.user_view = 'new'
            st.rerun()

        st.markdown("---")
        st.header("📜 Ticket History")
        try:
            tickets_df = ticket_service.get_user_tickets(st.session_state.user['username'])
            if tickets_df.empty:
                st.info("No previous tickets.")
            else:
                for _, ticket in tickets_df.iterrows():
                    title = ticket['title']
                    if len(title) > 14:
                        title = title[:11] + "..."
                    status = ticket['resolution_status']
                    dot_color = "🟢" if status == "resolved" else "🟡" if status == "tentative" else "🔴"
                    
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([0.6, 0.2, 0.2], gap="small")
                        with col1:
                            button_label = f"{dot_color} {title}"
                            if st.button(button_label, key=f"btn_ticket_{ticket['id']}", use_container_width=True):
                                st.session_state.user_view = ticket['id']
                                st.rerun()
                        with col2:
                            if st.button("✏️", key=f"edit_ticket_{ticket['id']}", use_container_width=True):
                                st.session_state.user_view = f"edit_{ticket['id']}"
                                st.rerun()
                        with col3:
                            if st.button("🗑️", key=f"delete_ticket_{ticket['id']}", use_container_width=True):
                                ticket_service.delete_ticket(ticket['id'])
                                if st.session_state.user_view == ticket['id'] or str(st.session_state.user_view) == f"edit_{ticket['id']}":
                                    st.session_state.user_view = 'new'
                                st.rerun()
        except Exception as e:
            st.error(f"Error loading history: {str(e)}")

        st.markdown("---")
        st.header("⚙️ Settings")
        
        with st.expander("👤 Edit Username"):
            with st.form("change_username_form"):
                new_usr = st.text_input("New Username")
                usr_pwd = st.text_input("Verify Password", type="password")
                if st.form_submit_button("Update Username", use_container_width=True):
                    if not new_usr or not usr_pwd:
                        st.error("Please fill all fields.")
                    else:
                        if auth_service.change_username(st.session_state.user['username'], new_usr, usr_pwd):
                            st.session_state.user['username'] = new_usr
                            st.success("Username updated successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Incorrect password or username already taken.")

        with st.expander("✏️ Edit Password"):
            with st.form("change_password_form"):
                old_pwd = st.text_input("Current Password", type="password")
                new_pwd = st.text_input("New Password", type="password")
                confirm_pwd = st.text_input("Confirm New Password", type="password")
                if st.form_submit_button("Update Password", use_container_width=True):
                    if new_pwd != confirm_pwd:
                        st.error("New passwords do not match!")
                    elif not old_pwd or not new_pwd:
                        st.error("Please fill all fields.")
                    else:
                        if auth_service.change_password(st.session_state.user['username'], old_pwd, new_pwd):
                            st.success("Password updated successfully!")
                        else:
                            st.error("Incorrect current password or update failed.")

        if st.button("🗑️ Delete Account", use_container_width=True):
            st.session_state.confirm_delete = True
            
        if st.session_state.get('confirm_delete', False):
            st.warning("⚠️ Are you sure you want to delete your account? This action cannot be undone.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete", type="primary", use_container_width=True):
                    if auth_service.delete_user(st.session_state.user['username']):
                        del st.session_state.user
                        if 'confirm_delete' in st.session_state:
                            del st.session_state.confirm_delete
                        st.session_state.page = "login"
                        st.rerun()
            with col2:
                if st.button("Cancel", use_container_width=True):
                    del st.session_state.confirm_delete
                    st.rerun()

    if st.session_state.user_view == 'new':
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        render_knowledge_base_expander()
        render_new_incident()
        st.markdown('</div>', unsafe_allow_html=True)
    elif str(st.session_state.user_view).startswith('edit_'):
        ticket_id = int(str(st.session_state.user_view).replace('edit_', ''))
        try:
            ticket = ticket_service.get_ticket_by_id(ticket_id)
            if ticket:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.header("✏️ Edit Incident")
                if st.button("← Cancel Edit"):
                    st.session_state.user_view = ticket_id
                    st.rerun()
                with st.form("edit_ticket_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        title = st.text_input("Issue Title", value=ticket['title'])
                        category = st.selectbox(
                            "Category",
                            ["Technical", "Billing", "Account", "General", "Other"],
                            index=["Technical", "Billing", "Account", "General", "Other"].index(ticket['category']) if ticket['category'] in ["Technical", "Billing", "Account", "General", "Other"] else 0
                        )
                    with col2:
                        priority = st.selectbox(
                            "Priority",
                            ["Low", "Medium", "High", "Critical"],
                            index=["Low", "Medium", "High", "Critical"].index(ticket['priority']) if ticket['priority'] in ["Low", "Medium", "High", "Critical"] else 0
                        )
                    description = st.text_area("Detailed Description", value=ticket['description'], height=150)
                    submit_button = st.form_submit_button("💾 Save Changes", use_container_width=True)

                    if submit_button:
                        if not title or not description:
                            st.error("Please fill in title and description.")
                        else:
                            with st.spinner("Re-analyzing and updating..."):
                                try:
                                    ticket_service.update_ticket(ticket_id, title, description, category, priority)
                                    st.success("✅ Ticket updated successfully!")
                                    st.session_state.user_view = ticket_id
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating ticket: {str(e)}")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error("Ticket not found.")
                if st.button("← Go Back"):
                    st.session_state.user_view = 'new'
                    st.rerun()
        except Exception as e:
            st.error(f"Error loading ticket info: {str(e)}")
    else:
        ticket_id = st.session_state.user_view
        try:
            ticket = ticket_service.get_ticket_by_id(ticket_id)
            if ticket:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.header("🎟️ Ticket Details")
                if st.button("← Back"):
                    st.session_state.user_view = 'new'
                    st.rerun()
                st.markdown("---")
                render_ticket_card(ticket_service, ticket, st.session_state.user['username'])
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error("Ticket not found.")
                if st.button("← Go Back"):
                    st.session_state.user_view = 'new'
                    st.rerun()
        except Exception as e:
            st.error(f"Error loading ticket info: {str(e)}")
