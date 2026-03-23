"""
Main Streamlit application entry point.
Handles multi-page routing with simple 12-page structure.
"""

import streamlit as st
from pathlib import Path

from Auth.auth import init_session_state
from Auth.db import init_db
from utils.config import (
    PAGE_ICON,
    PAGE_TITLE,
    LAYOUT,
    INITIAL_SIDEBAR_STATE,
)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title=f"{PAGE_ICON} {PAGE_TITLE}",
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state=INITIAL_SIDEBAR_STATE,
    menu_items={
        "Get Help": "https://github.com/your-repo/issues",
        "Report a bug": "https://github.com/your-repo/issues",
        "About": f"{PAGE_TITLE} v3.0 - Phase 5"
    }
)

# ============================================================================
# GLOBAL INITIALIZATION
# ============================================================================

init_db()
init_session_state()

# ============================================================================
# ENHANCED GLOBAL STYLING
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    :root {
        --primary: #667eea;
        --primary-dark: #764ba2;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
        --bg-light: #f9fafb;
        --border-light: #e5e7eb;
    }
    
    .main {
        padding: 2.5rem 2rem;
        background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
    }
    
    h1 {
        color: var(--text-primary);
        border-bottom: 3px solid var(--primary);
        padding-bottom: 1rem;
        margin-bottom: 2rem;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    h2 {
        color: var(--text-primary);
        border-bottom: 2px solid var(--primary);
        padding-bottom: 0.75rem;
        margin-bottom: 1.5rem;
        font-size: 1.8rem;
        font-weight: 600;
    }
    
    h3 {
        color: var(--text-primary);
        margin-bottom: 1rem;
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    p, li {
        color: var(--text-secondary);
        line-height: 1.6;
        font-size: 0.95rem;
    }
    
    a {
        color: var(--primary);
        text-decoration: none;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    a:hover {
        color: var(--primary-dark);
        text-decoration: underline;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 0.75rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    
    .stMetric {
        background: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        border-left: 4px solid var(--primary);
    }
    
    .stExpander {
        border: 1px solid var(--border-light) !important;
        border-radius: 0.75rem !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
    }
    
    .stAlert {
        border-radius: 0.75rem !important;
        border-left: 4px solid;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .stDataFrame {
        border-radius: 0.75rem;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
    
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-light), transparent);
        margin: 2rem 0;
    }
    
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg-light); }
    ::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--primary-dark); }
    
    * { transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# ENHANCED SIDEBAR - CLEAN 12-PAGE NAVIGATION
# ============================================================================

with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 1.5rem 0;'>
        <h1 style='font-size: 2.5rem; border: none; margin: 0; color: #FFFFFF;'>🛡️</h1>
        <h2 style='font-size: 1.1rem; margin: 0.5rem 0; color: #FFFFFF; border: none; padding: 0;'>PPE Platform</h2>
        <p style='color: #FFFFFF; font-size: 0.8rem; margin: 0.5rem 0 0 0;'>v3.0 | Phase 5</p>
    </div>
    """, unsafe_allow_html=True)
    
    
    
    st.markdown("---")
    
    st.markdown("""
    <h3 style='color: #FFFFFF; font-size: 0.9rem; font-weight: 600; margin-bottom: 1rem; letter-spacing: 0.05em;'>ℹ️ ABOUT</h3>
    """, unsafe_allow_html=True)
    
    st.info(
        "**PPE Detection & Compliance Platform**\n\n"
        "Enterprise-grade safety monitoring system using YOLOv11 AI.\n\n"
        "**Features:**\n"
        "- Real-time PPE detection\n"
        "- Multi-tenant support\n"
        "- Advanced analytics\n"
        "- Secure authentication\n\n"
    )

# ============================================================================
# MAIN APP FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; font-size: 0.8rem; padding: 2rem 0; border-top: 1px solid #eee;'>
    <p style='margin: 0.5rem 0;'>🛡️ <strong>PPE Detection & Compliance Platform</strong></p>
    <p style='margin: 0.5rem 0;'>Powered by YOLOv11 | Built with Streamlit & SQLAlchemy</p>
    <p style='margin: 0.5rem 0;'>© 2024 | Phase 5: Live Detection and Security</p>
    <p style='margin: 0.5rem 0;'>🎯 <strong>12-Page Architecture</strong> • Modular Design</p>
</div>
""", unsafe_allow_html=True)
