"""
Home page (1_🏠_Home.py) - Landing page with login redirect and welcome dashboard.
Displays different content based on authentication status.
"""

import streamlit as st
from datetime import datetime

from Auth.auth import (
    init_session_state,
    is_authenticated,
    require_auth,
    get_current_user_id,
    get_session_data,
    get_user_organizations,
    logout_user
)
from Auth.db import (
    init_db,
    get_user_by_id,
    get_organization_members,
    get_workstations_by_organization
)
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
)

# ============================================================================
# INITIALIZATION
# ============================================================================

init_db()
init_session_state()

# ============================================================================
# CUSTOM STYLING - FIXED TEXT VISIBILITY
# ============================================================================

st.markdown("""
<style>
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .hero-section h1 {
        color: white !important;
        border: none !important;
        margin: 0;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .hero-section p {
        font-size: 1.1rem;
        opacity: 0.95;
        margin: 0;
        color: white !important;
    }
    
    .feature-card {
        background: white;
        border-radius: 0.75rem;
        padding: 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        text-align: center;
        border-top: 4px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.2);
    }
    
    .feature-card h3 {
        color: #1f2937 !important;
        border: none !important;
        padding: 0 !important;
        margin-bottom: 0.5rem !important;
        font-size: 1.3rem !important;
        font-weight: 600 !important;
    }
    
    .feature-card p {
        color: #6b7280 !important;
        font-size: 0.95rem !important;
        margin: 0 !important;
        line-height: 1.5 !important;
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    
    .stat-card {
        background: white;
        border-radius: 0.75rem;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #667eea !important;
    }
    
    .stat-label {
        color: #666 !important;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    .info-text {
        color: #1f2937 !important;
        font-size: 0.95rem !important;
    }
    
    .step-heading {
        font-weight: 600 !important;
        color: #1f2937 !important;
        margin-bottom: 0.5rem !important;
    }
    
    .step-text {
        color: #6b7280 !important;
        font-size: 0.9rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# PAGE CONTENT
# ============================================================================

if not is_authenticated():
    # ========================================================================
    # NOT AUTHENTICATED - LANDING PAGE
    # ========================================================================
    
    st.markdown("""
    <div class='hero-section'>
        <h1>🛡️ PPE Detection Platform</h1>
        <p>Real-time Safety Compliance Monitoring</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("## Welcome to Advanced PPE Detection")
    
    st.markdown("""
    <p class='info-text'>
    Protect your workforce with AI-powered personal protective equipment compliance monitoring.
    Real-time detection, instant alerts, and comprehensive compliance reports.
    </p>
    """, unsafe_allow_html=True)
    
    # Features Section
    st.markdown("## ✨ Key Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🎯</div>
            <h3>Real-time Detection</h3>
            <p>Instant PPE identification with 99% accuracy using YOLOv11</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>📊</div>
            <h3>Analytics Dashboard</h3>
            <p>Comprehensive compliance metrics and historical trends</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🏢</div>
            <h3>Multi-Tenant</h3>
            <p>Manage multiple organizations and workstations seamlessly</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # CTA Section
    st.markdown("## 🚀 Get Started Now")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>👤</div>
            <h3>Create Account</h3>
            <p>Sign up for free and join thousands of safety-conscious organizations</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📝 Register Now", key="register_btn", use_container_width=True, type="primary"):
            st.session_state.auth_tab = "register"
            st.switch_page("pages/5_🔐_Account.py")
    
    with col2:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🔓</div>
            <h3>Existing User?</h3>
            <p>Sign in to your account to access your organization's data</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔐 Login", key="login_btn", use_container_width=True, type="primary"):
            st.session_state.auth_tab = "login"
            st.switch_page("pages/5_🔐_Account.py")
    
    st.markdown("---")
    
    # Stats Section
    st.markdown("## 📈 By The Numbers")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-number'>99%</div>
            <div class='stat-label'>Detection Accuracy</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-number'>5</div>
            <div class='stat-label'>PPE Classes</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-number'>24/7</div>
            <div class='stat-label'>Monitoring</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-number'>∞</div>
            <div class='stat-label'>Scalability</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Info Section
    st.markdown("## 📋 How It Works")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <p class='step-heading'>1️⃣ Upload or Stream</p>
        <p class='step-text'>Provide images or live video feeds from your workstations</p>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <p class='step-heading'>2️⃣ AI Detection</p>
        <p class='step-text'>Our YOLOv11 model identifies PPE items in real-time</p>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <p class='step-heading'>3️⃣ Get Insights</p>
        <p class='step-text'>View compliance status and detailed analytics instantly</p>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    <div style='text-align: center; padding: 2rem; color: #666;'>
        <p><strong>Ready to enhance workplace safety?</strong></p>
        <p>Use the buttons above to get started or navigate to <strong>Account</strong> in the sidebar</p>
    </div>
    """, unsafe_allow_html=True)

else:
    # ========================================================================
    # AUTHENTICATED - WELCOME DASHBOARD
    # ========================================================================
    
    session_data = get_session_data()
    
    st.markdown(f"""
    <div class='hero-section'>
        <h1>Welcome back, {session_data['name']}! 👋</h1>
        <p>{datetime.now().strftime("%A, %B %d, %Y")}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick Stats
    st.markdown("## 📊 Quick Stats")
    
    user_orgs = get_user_organizations()
    total_members = sum(len(get_organization_members(org.id)) for org in user_orgs)
    total_workstations = sum(len(get_workstations_by_organization(org.id)) for org in user_orgs)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="🏢 Organizations", value=len(user_orgs))
    with col2:
        st.metric(label="👥 Team Members", value=total_members)
    with col3:
        st.metric(label="📷 Workstations", value=total_workstations)
    with col4:
        st.metric(label="🎯 Active Status", value="✅ Online")
    
    st.markdown("---")
    
    # Current Organization
    if session_data['org_id']:
        st.markdown(f"## 🏢 Current Organization: **{session_data['org_name']}**")
        
        current_org = next((org for org in user_orgs if org.id == session_data['org_id']), None)
        
        if current_org:
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**Description:** {current_org.description or 'No description'}")
            
            with col2:
                st.success(f"**Created:** {current_org.created_at.strftime('%B %d, %Y')}")
    else:
        st.warning("⚠️ Please select or create an organization to proceed.")
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("## ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>📷</div>
            <h3>Detection</h3>
            <p>Run PPE detection on images or video</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Detection", key="detection_btn", use_container_width=True):
            st.switch_page("pages/3_📷_Detection.py")
    
    with col2:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>📊</div>
            <h3>Dashboard</h3>
            <p>View compliance analytics</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View Dashboard", key="dashboard_btn", use_container_width=True):
            st.switch_page("pages/2_📊_Dashboard.py")
    
    with col3:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🏢</div>
            <h3>Organizations</h3>
            <p>Manage your teams</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Manage Teams", key="org_btn", use_container_width=True):
            st.switch_page("pages/4_🏢_Organizations.py")
    
    st.markdown("---")
    
    # Footer
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**PPE Detection & Compliance Platform** | Phase 1: Authentication & Detection")
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()