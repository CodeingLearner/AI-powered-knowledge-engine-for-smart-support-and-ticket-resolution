import html # used for escaping html - render raw html directly 
import re 
import auth_service
import streamlit as st
import ticket_service

st.set_page_config(
    page_title="AI Support Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)


@st.cache_resource
def init_app():
    ticket_service.initialize_system()
    auth_service.create_default_users()

init_app()

st.markdown("""
<style>)
    @import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap");
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #e2e8f0;
    }

    .stApp{
    background:
        radial-gradient(circle at top left, rgba(37, 99, 235, 0.18), transparent 35%),
        radial-gradient(circle at top right, rgba(14, 165, 233, 0.16), transparent 30%),
        #0f1116;

    }
    .block-container{
         max-width: 1200px;
         padding-top: 2.5 rem; 
         }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    div[data-baseweb = "select"] > div {
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    .ticket-card{
        background-color: rgba(15, 23, 42, 0.88);
        border: 1px solid #334155;
        border-radius: 8px;
        font-weight: 600;
    }
    
    .metric-card{
        background-color: rgba(15, 23, 42, 0.88);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        }
    
    .chip{
        display: inline-block;
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-right: 0.4rem; 
        }
</style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state["user"] = None
if "lastest_submitted_ticket_id" not in st.session_state:
    st.session_state["lastest_submitted_ticket_id"] = None

def auth_page():
    st.title("Welcome to AI Support")
    st.markdown("Your intelligent technical resolution partner.")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        with st.form("login_form"):
            st.subheader("Sign In")
            username = st.text_input("Username")
            password = st.text_input("Password", type = "password")
            submit = st.form_submit_button("Access Account")

            if submit:
                if username and password:
                    user = auth_service.login_user(username, password)
                    if user:
                        st.session_state["user"] = user
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.warning("Please enter both username and password")
    
    with tab2:
        with st.form("signup_form"):
            st.subheader("Create Account")
            new_user = st.text_input("Enter Username")
            new_pass = st.text_input("Enter Password", type = "password")
            confirm_pass = st.text_input("Confirm Password", type = "password")
            submit_signup = st.form_submit_button("Register")

            if submit_signup:
                if new_user and new_pass and cofirm_pass:
                    if new_pass != confirm_pass:
                        st.error("Passwords do not match.")
                    elif auth_service.register_user(new_user, new_pass):
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error("Username already exists.")
                else:
                    st.warning("Please fill in all fields.")

def  confidence_label(score):
    if score > 0.75:
        return "High confidence", "#22c55e"
    if score >= 0.45:
        return "Tentative", "#f59e0b"
    return "Low confidence", "#ef4444"

def normalize_Resolution_markdown(text):
    if not text:
        return ""
    
    cleaned_text = re.sub(
        r"<div[^>]*>\s*AI Resolution\s*</div>",
        "",
        str(text),
        flags = re.IGNORECASE,
    ).strip()

    if len(cleaned_text) >= 2 and cleaned_text[0] == cleaned_text[-1] and cleaned_text[0] in {'"', "'"}: #"AI RESULTION" -> AI RESULTION
        cleaned_text = cleaned_text[1:-1].strip()
       

    normalized_lines = []
    for line in cleaned_text.splitlines():
        stripped = line.lstrip() #          AI RESOLUTION -> AI RESOLUTION
        indent = line[: len(line) - len(stripped)] # 16 - 12 = 4  Line[:4]= 0,1,2,3 -> 4 space = "        "

        if stripped.startswith(("* ","â€¢ ")): #**  AI RESULTION
            normalized_lines.append(f"{indent} - {stripped[2:].lstrip()}")
        
        if re.match(r"^\d+\)\s+", stripped):
            normalized_lines.append(f"{indent}{re.sub(r'^(\d+)\)\s+',r'\\1.',  stripped)}") # 1) hi -> 1. hi
            continue

        normalized_lines.append(line)
    return "\n".join(normalized_lines).strip()


def render_feedback_controls(ticket, user_id , render_context = "default"):
    if ticket.get("feedback_value"):
        st.caption(f"Feedback recorded: '{ticket['feedback_value']}'")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            " 👍 Helpful",
            key =f"helpful-{ticket['id']}_{render_context}",
            width="stretch",
        ):
            if ticket_service.submit_feedback(ticket["id"], "helpful", user_id):
                st.rerun()
    
    with col2:
        if st.button(
            " 👎 Not helpful",
            key =f"not_helpful-{ticket['id']}_{render_context}",
            width="stretch",
        ):
            if ticket_service.submit_feedback(ticket["id"], "not_helpful", user_id):
                st.rerun()

def render_ticket_card(ticket, user_id=None, show_feedback=False, render_context="default"):
    label, label_color = confidence_label(ticket.get("confidence_score") or 0.0)
    category_color = "#38bdf8" if ticket["category"] in ["Network", "Security", " Hardware"] else "#f59e0b"
    priority_color = "#ef4444" if ticket["priority"] in ["High", "Critical"] else "#22c55e"
    status = ticket.get("resolution_status","unresolved")
    resolution_md = normalize_Resolution_markdown(ticket.get("ai_resolution", ""))
    safe_title = html.escape(ticket["title"]) 
    safe_desc = html.escape(ticket["description"])
    warning =""
    if status == "tentative":
        warning = "<p style='color: #fbbf24; margin-top: 0.75rem; '> Low confidence: review  this suggestion before treating it as final guidance.</p>"
    elif status == "unresloved":
        warning = "<p style='color: #f87171; margin-top: 0.75rem; '> Unresolved: AI could not confidently resolve this ticket. Consider manual intervention.</p>"
    
    st.markdown(
        f"""
        <div class="ticket-card">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
                <h3 style="margin: 0; font-size: 1.1rem; color: #e2e8f0;">{safe_title}</h3>
                <span style="background-color: {category_color}; color: #0f1116; padding: 0.2rem 0.65rem; border-radius: 999px; font-size: 0.78rem; font-weight: 700; margin-right: 0.4rem; ">{ticket['category']}</span>
            </div>
            <p style="margin: 0; color: #94a3b8; font-size: 0.9rem;">{safe_desc}</p>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.75rem;">
                <span style="background-color: {priority_color}; color: #0f1116; padding: 0.2rem 0.65rem; border-radius: 999px; font-size: 0.78rem; font-weight: 700; margin-right: 0.4rem; ">{ticket['priority']}</span>
                <span style="background-color: {label_color}; color: #0f1116; padding: 0.2rem 0.65rem; border-radius: 999px; font-size: 0.78rem; font-weight: 700; margin-right: 0.4rem; ">{label}</span>
            </div>
        </div>
    )
        
    
            
                                              
                                              

    