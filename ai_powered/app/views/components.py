import streamlit as st
import pandas as pd
import time

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

def render_ticket_card(ticket_service, ticket, username):
    """Renders a single ticket card with feedback options."""
    resolution_class = get_resolution_class(ticket['resolution_status'])
    confidence_class = get_confidence_class(ticket['confidence_score'])

    with st.container():
        st.markdown(f"""
        <div class="ticket-card {resolution_class}">
            <h4>{ticket['title']}</h4>
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
        """, unsafe_allow_html=True)
        
        if ticket.get('kb_context_found') and ticket.get('suggested_kb_filename'):
            st.markdown(f"""
            <details>
                <summary>📄 Source Document</summary>
                <p>Retrieved from: <strong>{ticket['suggested_kb_filename']}</strong></p>
            </details>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Feedback section
    if pd.isna(ticket.get('feedback_value')):
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"👍 Helpful", key=f"helpful_{ticket['id']}"):
                ticket_service.submit_feedback(ticket['id'], "helpful", username)
                st.success("Thank you for your feedback!")
                time.sleep(1)
                st.rerun()
        with col2:
            if st.button(f"👎 Not Helpful", key=f"not_helpful_{ticket['id']}"):
                ticket_service.submit_feedback(ticket['id'], "not_helpful", username)
                st.success("Thank you for your feedback!")
                time.sleep(1)
                st.rerun()
    else:
        st.caption(f"Feedback: {'👍 Helpful' if ticket['feedback_value'] == 'helpful' else '👎 Not Helpful'}")
