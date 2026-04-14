import streamlit as st

def inject_custom_css():
    st.markdown("""
<style>
    /* Global Background overrides just in case config.toml misses it for some containers */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
        font-family: 'Inter', 'Poppins', sans-serif;
    }
    
    /* Modern Glassmorphism Cards */
    .glass-card {
        background: rgba(30, 30, 30, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .ticket-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #3b82f6;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .ticket-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.4);
    }

    /* Status Colors for Left Borders */
    .resolution-resolved {
        border-left-color: #10b981; /* Green */
    }
    .resolution-tentative {
        border-left-color: #f59e0b; /* Yellow */
    }
    .resolution-unresolved {
        border-left-color: #ef4444; /* Red */
    }
    
    /* Text Status Colors */
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

    /* Minimal Input Styling */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        background-color: #181b21 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid #333 !important;
    }
    
    /* Button Aesthetics */
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #2563eb;
        transform: scale(1.02);
    }

    /* Hide standard sidebar padding */
    .css-1d391kg {
        padding-top: 3rem;
    }
    
    /* Metric Cards Override */
    div[data-testid="stMetricValue"] {
        font-weight: 700;
        font-size: 2rem;
    }

    /* Tab overrides */
    div[data-baseweb="tab-list"] {
        gap: 20px;
    }
    div[data-baseweb="tab"] {
        padding-top: 10px;
        padding-bottom: 10px;
        border-radius: 8px 8px 0 0;
    }
</style>
""", unsafe_allow_html=True)
