"""
Organizations page (4_🏢_Organizations.py) - Create and manage organizations and workstations.
PHASE 1.5: Full organization management with CRUD operations
"""

import streamlit as st
from datetime import datetime

from Auth.auth import (
    init_session_state,
    require_auth,
    get_current_user_id,
    get_session_data,
    get_user_organizations,
    set_active_organization,
)
from Auth.db import (
    init_db,
    create_organization,
    get_organization_by_id,
    update_organization,
    delete_organization,
    add_user_to_organization,
    get_organization_members,
    remove_user_from_organization,
    update_user_organization_role,
    create_workstation,
    get_workstations_by_organization,
    update_workstation,
    delete_workstation,
    get_user_by_id,
    get_user_by_email,
    create_audit_log,
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
    page_title="🏢 Organizations | PPE Detection Platform",
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state=INITIAL_SIDEBAR_STATE,
)

# ============================================================================
# INITIALIZATION
# ============================================================================

init_db()
init_session_state()

if not require_auth():
    st.stop()

# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
<style>
    .modal-box {
        background: white;
        border: 2px solid #dc3545;
        border-radius: 0.75rem;
        padding: 2rem;
        text-align: center;
    }
    
    .modal-title {
        color: #dc3545;
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    .modal-message {
        color: #666;
        margin-bottom: 1.5rem;
    }
    
    .danger-button {
        background-color: #dc3545;
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 0.5rem;
        border: none;
        cursor: pointer;
        font-weight: 600;
    }
    
    .info-box {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border: 2px solid #17a2b8;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .success-box {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 2px solid #28a745;
        border-radius: 0.75rem;
        padding: 1.5rem;
    }
    
    .member-card {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.75rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .workstation-card {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE FOR MODALS
# ============================================================================

if "delete_org_confirmation" not in st.session_state:
    st.session_state.delete_org_confirmation = None

if "delete_ws_confirmation" not in st.session_state:
    st.session_state.delete_ws_confirmation = None

if "edit_ws_mode" not in st.session_state:
    st.session_state.edit_ws_mode = {}

# ============================================================================
# HELPER: DELETE CONFIRMATION MODAL
# ============================================================================

def show_delete_confirmation(item_name: str, item_type: str) -> bool:
    """
    Show deletion confirmation modal.
    
    Args:
        item_name: Name of item to delete
        item_type: Type (Organization, Workstation, etc.)
        
    Returns:
        True if confirmed, False otherwise
    """
    st.markdown(f"""
    <div class='modal-box'>
        <div class='modal-title'>⚠️ Confirm Deletion</div>
        <div class='modal-message'>
            <strong>Are you sure you want to delete this {item_type}?</strong><br><br>
            <code>{item_name}</code><br><br>
            This action <strong>CANNOT</strong> be undone. All associated data will be permanently deleted.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🗑️ Delete", type="secondary", use_container_width=True, key=f"confirm_delete_{item_name}"):
            return True
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True, key=f"cancel_delete_{item_name}"):
            st.session_state.delete_org_confirmation = None
            st.session_state.delete_ws_confirmation = None
            st.rerun()
    
    return False

# ============================================================================
# PAGE CONTENT
# ============================================================================

st.title("🏢 Organizations & Workstations")

user_id = get_current_user_id()
session_data = get_session_data()
user_orgs = get_user_organizations()

# ============================================================================
# CREATE NEW ORGANIZATION SECTION
# ============================================================================

st.markdown("## ➕ Create New Organization")

with st.form("create_org_form", clear_on_submit=True):
    org_name = st.text_input(
        "Organization Name",
        placeholder="e.g., ABC Construction Inc.",
        help="Unique name for your organization",
        max_chars=255
    )
    
    org_description = st.text_area(
        "Description",
        placeholder="What does this organization do?",
        height=80,
        help="Optional description of your organization",
        max_chars=500
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        submit = st.form_submit_button(
            "✅ Create Organization",
            use_container_width=True,
            type="primary"
        )
    
    with col2:
        st.form_submit_button(
            "❌ Clear",
            use_container_width=True,
            type="secondary"
        )
    
    if submit:
        if not org_name:
            st.error("❌ Organization name is required")
        else:
            new_org = create_organization(
                name=org_name,
                admin_user_id=user_id,
                description=org_description if org_description else None
            )
            
            if new_org:
                # Auto-add creator as admin
                add_user_to_organization(user_id, new_org.id, role="Admin")
                
                # Create audit log
                create_audit_log(
                    org_id=new_org.id,
                    user_id=user_id,
                    action="organization_created",
                    resource_type="organization",
                    resource_id=new_org.id,
                    description=f"Organization '{org_name}' created"
                )
                
                st.success(f"✅ Organization '{org_name}' created successfully!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Organization name already exists. Please choose another name.")

# ============================================================================
# ORGANIZATIONS LIST
# ============================================================================

st.markdown("---")
st.markdown("## 📋 Your Organizations")

if not user_orgs:
    st.info("👆 Create an organization above to get started!")
else:
    # Sidebar selector
    org_names = [org.name for org in user_orgs]
    selected_org_name = st.selectbox(
        "Select Organization",
        org_names,
        key="org_selector",
        help="Choose an organization to manage"
    )
    
    selected_org = next(org for org in user_orgs if org.name == selected_org_name)
    
    # Quick action button
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        if st.button("✨ Select Active", use_container_width=True):
            set_active_organization(selected_org.id, selected_org.name)
            st.success(f"✅ Active organization: {selected_org.name}")
            st.rerun()
    
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # ====================================================================
    # ORGANIZATION DETAILS
    # ====================================================================
    
    st.markdown(f"### 🏢 {selected_org.name}")
    
    # KPI Cards
    members = get_organization_members(selected_org.id)
    workstations = get_workstations_by_organization(selected_org.id)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="👥 Members",
            value=len(members),
            delta="Total"
        )
    
    with col2:
        st.metric(
            label="📷 Workstations",
            value=len(workstations),
            delta="Detection points"
        )
    
    with col3:
        admin_user = get_user_by_id(selected_org.admin_user_id)
        st.metric(
            label="👨‍💼 Admin",
            value=admin_user.name if admin_user else "Unknown"
        )
    
    st.markdown("---")
    
    # ====================================================================
    # ORGANIZATION TABS
    # ====================================================================
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Details", "👥 Members", "📷 Workstations", "📋 Audit"])
    
    # ========== TAB 1: DETAILS ==========
    with tab1:
        st.markdown("#### Organization Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {selected_org.name}")
            st.write(f"**Description:** {selected_org.description or 'No description'}")
        
        with col2:
            st.write(f"**ID:** `{selected_org.id}`")
            st.write(f"**Created:** {selected_org.created_at.strftime('%B %d, %Y')}")
        
        # Edit organization
        st.markdown("#### Edit Organization")
        
        with st.form("edit_org_form"):
            new_name = st.text_input("Name", value=selected_org.name)
            new_description = st.text_area("Description", value=selected_org.description or "")
            
            submit = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
            
            if submit:
                if new_name != selected_org.name or new_description != (selected_org.description or ""):
                    updated = update_organization(
                        selected_org.id,
                        name=new_name,
                        description=new_description
                    )
                    if updated:
                        # Create audit log
                        create_audit_log(
                            org_id=selected_org.id,
                            user_id=user_id,
                            action="organization_updated",
                            resource_type="organization",
                            resource_id=selected_org.id,
                            changes={"name": (selected_org.name, new_name), "description": (selected_org.description, new_description)},
                            description="Organization details updated"
                        )
                        
                        st.success("✅ Organization updated!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update organization")
                else:
                    st.info("ℹ️ No changes made")
        
        # Delete organization
        st.markdown("#### Danger Zone")
        
        # ✅ FEATURE 1: DELETE ORGANIZATION WITH CONFIRMATION
        if st.button("🗑️ Delete Organization", type="secondary", use_container_width=True, key="btn_delete_org"):
            st.session_state.delete_org_confirmation = selected_org.id
        
        # Show confirmation modal if active
        if st.session_state.delete_org_confirmation == selected_org.id:
            st.markdown("---")
            if show_delete_confirmation(selected_org.name, "Organization"):
                try:
                    success = delete_organization(selected_org.id)
                    if success:
                        # Create audit log
                        create_audit_log(
                            org_id=selected_org.id,
                            user_id=user_id,
                            action="organization_deleted",
                            resource_type="organization",
                            resource_id=selected_org.id,
                            description=f"Organization '{selected_org.name}' deleted"
                        )
                        
                        st.success(f"✅ Organization '{selected_org.name}' deleted successfully!")
                        st.session_state.delete_org_confirmation = None
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete organization")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # ========== TAB 2: MEMBERS ==========
    with tab2:
        st.markdown("#### 👥 Organization Members")
        
        if members:
            # Members list
            st.markdown("##### Current Members")
            
            for member in members:
                user = get_user_by_id(member.user_id)
                if user:
                    with st.expander(f"👤 {user.name} ({member.role})", expanded=False):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**Email:** {user.email}")
                            st.write(f"**Joined:** {member.joined_at.strftime('%B %d, %Y')}")
                        
                        with col2:
                            st.write(f"**Current Role:** {member.role}")
                        
                        with col3:
                            # ✅ FEATURE 2: UPDATE MEMBER ROLE (Admin only)
                            if user.id != user_id and member.role != "Admin":  # Can't change own role or admin's role
                                new_role = st.selectbox(
                                    "Change Role",
                                    ["Viewer", "Supervisor"],
                                    index=["Viewer", "Supervisor"].index(member.role) if member.role in ["Viewer", "Supervisor"] else 0,
                                    key=f"role_{member.user_id}",
                                    help="Update member's role in this organization"
                                )
                                
                                if st.button("💾 Update Role", use_container_width=True, key=f"update_role_{member.user_id}"):
                                    updated = update_user_organization_role(user.id, selected_org.id, new_role)
                                    if updated:
                                        # Create audit log
                                        create_audit_log(
                                            org_id=selected_org.id,
                                            user_id=user_id,
                                            action="member_role_updated",
                                            resource_type="member",
                                            resource_id=user.id,
                                            changes={"role": (member.role, new_role)},
                                            description=f"Role updated for {user.name}"
                                        )
                                        
                                        st.success(f"✅ {user.name}'s role updated to {new_role}")
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to update role")
                            
                            # Remove member button (Admin only)
                            if user.id != user_id:
                                if st.button("❌ Remove", use_container_width=True, key=f"remove_{member.user_id}"):
                                    removed = remove_user_from_organization(user.id, selected_org.id)
                                    if removed:
                                        # Create audit log
                                        create_audit_log(
                                            org_id=selected_org.id,
                                            user_id=user_id,
                                            action="member_removed",
                                            resource_type="member",
                                            resource_id=user.id,
                                            description=f"{user.name} removed from organization"
                                        )
                                        
                                        st.success(f"✅ {user.name} removed from organization")
                                        st.rerun()
        else:
            st.info("No members yet")
        
        st.markdown("---")
        st.markdown("#### ➕ Invite New Member")
        
        # ✅ FEATURE 2: INVITE MEMBERS
        with st.form("invite_member_form", clear_on_submit=True):
            member_email = st.text_input(
                "Member Email",
                placeholder="user@example.com",
                help="Email of existing user to invite"
            )
            
            member_role = st.selectbox(
                "Role",
                ["Viewer", "Supervisor"],
                help="Select role in this organization"
            )
            
            submit_invite = st.form_submit_button("📧 Send Invite", use_container_width=True, type="primary")
            
            if submit_invite:
                if not member_email:
                    st.error("❌ Please enter an email address")
                else:
                    # Check if user exists
                    invite_user = get_user_by_email(member_email.strip())
                    if not invite_user:
                        st.error("❌ User with this email does not exist. They must register first.")
                    else:
                        # Check if already in organization
                        existing_member = next(
                            (m for m in members if get_user_by_id(m.user_id).email == member_email.strip()),
                            None
                        )
                        if existing_member:
                            st.warning("⚠️ This user is already a member of this organization")
                        else:
                            # Add user to organization
                            added = add_user_to_organization(invite_user.id, selected_org.id, member_role)
                            if added:
                                # Create audit log
                                create_audit_log(
                                    org_id=selected_org.id,
                                    user_id=user_id,
                                    action="member_invited",
                                    resource_type="member",
                                    resource_id=invite_user.id,
                                    description=f"{invite_user.name} ({member_role}) invited to organization"
                                )
                                
                                st.success(f"✅ {invite_user.name} added as {member_role}!")
                                st.info("💡 They can now access this organization")
                                st.rerun()
                            else:
                                st.error("❌ Failed to add member")
    
    # ========== TAB 3: WORKSTATIONS ==========
    with tab3:
        st.markdown("#### 📷 Workstations")
        
        # Create workstation form
        st.markdown("##### ➕ Add New Workstation")
        
        with st.form("create_workstation_form", clear_on_submit=True):
            ws_name = st.text_input(
                "Workstation Name",
                placeholder="e.g., Main Gate, Factory Floor",
                help="Name of detection point",
                max_chars=255
            )
            
            ws_description = st.text_area(
                "Description",
                placeholder="Where is this workstation located?",
                height=80,
                help="Optional description",
                max_chars=500
            )
            
            ws_camera_url = st.text_input(
                "Camera URL (Optional)",
                placeholder="http://192.168.1.100:8080/video",
                help="IP camera stream URL for Phase 3",
                max_chars=500
            )
            
            submit_ws = st.form_submit_button("✅ Create Workstation", use_container_width=True, type="primary")
            
            if submit_ws:
                if not ws_name:
                    st.error("❌ Workstation name is required")
                else:
                    new_ws = create_workstation(
                        org_id=selected_org.id,
                        name=ws_name,
                        description=ws_description if ws_description else None,
                        camera_url=ws_camera_url if ws_camera_url else None,
                    )
                    
                    if new_ws:
                        # Create audit log
                        create_audit_log(
                            org_id=selected_org.id,
                            user_id=user_id,
                            action="workstation_created",
                            resource_type="workstation",
                            resource_id=new_ws.id,
                            description=f"Workstation '{ws_name}' created"
                        )
                        
                        st.success("✅ Workstation created!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Failed to create workstation")
        
        st.markdown("---")
        st.markdown("##### 📋 Workstations List")
        
        if workstations:
            for ws in workstations:
                st.markdown(f"###### 📷 {ws.name} {'🟢' if ws.is_active else '🔴'}")
                
                # Display workstation info
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Description:** {ws.description or 'N/A'}")
                    st.write(f"**Camera:** {ws.camera_url or 'Not configured'}")
                
                with col2:
                    st.write(f"**Status:** {'🟢 Active' if ws.is_active else '🔴 Inactive'}")
                    st.write(f"**Created:** {ws.created_at.strftime('%b %d, %Y')}")
                
                with col3:
                    st.write(f"**ID:** `{ws.id}`")
                
                # ✅ FEATURE 3: EDIT WORKSTATION DETAILS
                st.markdown("**Actions:**")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button(
                        f"✏️ Edit",
                        key=f"edit_ws_{ws.id}",
                        use_container_width=True
                    ):
                        st.session_state.edit_ws_mode[ws.id] = True
                
                with col2:
                    if st.button(
                        f"{'🔴 Deactivate' if ws.is_active else '🟢 Activate'}",
                        key=f"toggle_ws_{ws.id}",
                        use_container_width=True
                    ):
                        updated = update_workstation(ws.id, is_active=not ws.is_active)
                        if updated:
                            # Create audit log
                            create_audit_log(
                                org_id=selected_org.id,
                                user_id=user_id,
                                action="workstation_toggled",
                                resource_type="workstation",
                                resource_id=ws.id,
                                changes={"is_active": (ws.is_active, not ws.is_active)},
                                description=f"Workstation '{ws.name}' {'deactivated' if ws.is_active else 'activated'}"
                            )
                            
                            st.success(f"✅ Workstation {'deactivated' if ws.is_active else 'activated'}")
                            st.rerun()
                
                with col3:
                    if st.button(f"📊 Stats", key=f"stats_ws_{ws.id}", use_container_width=True):
                        st.info("📊 Workstation statistics coming in Phase 4")
                
                with col4:
                    if st.button(f"🗑️ Delete", key=f"delete_ws_btn_{ws.id}", use_container_width=True):
                        st.session_state.delete_ws_confirmation = ws.id
                
                # Show edit form if in edit mode
                if st.session_state.edit_ws_mode.get(ws.id, False):
                    st.markdown("**Edit Workstation Details:**")
                    
                    with st.form(f"edit_ws_form_{ws.id}"):
                        edit_name = st.text_input("Name", value=ws.name, max_chars=255)
                        edit_description = st.text_area("Description", value=ws.description or "", max_chars=500)
                        edit_camera_url = st.text_input("Camera URL", value=ws.camera_url or "", max_chars=500)
                        
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            if st.form_submit_button("💾 Save", use_container_width=True, type="primary"):
                                updated = update_workstation(
                                    ws.id,
                                    name=edit_name,
                                    description=edit_description if edit_description else None,
                                    camera_url=edit_camera_url if edit_camera_url else None
                                )
                                
                                if updated:
                                    # Create audit log
                                    create_audit_log(
                                        org_id=selected_org.id,
                                        user_id=user_id,
                                        action="workstation_updated",
                                        resource_type="workstation",
                                        resource_id=ws.id,
                                        changes={
                                            "name": (ws.name, edit_name),
                                            "description": (ws.description, edit_description),
                                            "camera_url": (ws.camera_url, edit_camera_url)
                                        },
                                        description=f"Workstation '{ws.name}' configuration updated"
                                    )
                                    
                                    st.success("✅ Workstation updated!")
                                    st.session_state.edit_ws_mode[ws.id] = False
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to update")
                        
                        with col2:
                            if st.form_submit_button("❌ Cancel", use_container_width=True):
                                st.session_state.edit_ws_mode[ws.id] = False
                                st.rerun()
                
                # Show deletion confirmation if active
                if st.session_state.delete_ws_confirmation == ws.id:
                    if show_delete_confirmation(ws.name, "Workstation"):
                        success = delete_workstation(ws.id)
                        if success:
                            # Create audit log
                            create_audit_log(
                                org_id=selected_org.id,
                                user_id=user_id,
                                action="workstation_deleted",
                                resource_type="workstation",
                                resource_id=ws.id,
                                description=f"Workstation '{ws.name}' deleted"
                            )
                            
                            st.success(f"✅ Workstation '{ws.name}' deleted successfully!")
                            st.session_state.delete_ws_confirmation = None
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete workstation")
                
                st.markdown("---")
        else:
            st.info("👆 Create a workstation above to start detecting PPE!")
    
    # ========== TAB 4: AUDIT LOG ==========
    with tab4:
        st.markdown("#### 📋 Organization Audit Log")
        
        from Auth.db import get_org_audit_logs
        
        try:
            audit_logs = get_org_audit_logs(selected_org.id, limit=50)
            
            if not audit_logs:
                st.info("📭 No audit logs found")
            else:
                st.markdown(f"##### Last {len(audit_logs)} Actions")
                
                for log in audit_logs:
                    action_emoji_map = {
                        "organization_created": "🏢",
                        "organization_updated": "✏️",
                        "organization_deleted": "🗑️",
                        "member_invited": "👥",
                        "member_role_updated": "🔄",
                        "member_removed": "❌",
                        "workstation_created": "📷",
                        "workstation_updated": "✏️",
                        "workstation_deleted": "🗑️",
                        "workstation_toggled": "🔘",
                    }
                    
                    emoji = action_emoji_map.get(log.action, "📝")
                    action_name = log.action.replace("_", " ").title()
                    
                    with st.expander(f"{emoji} {action_name} - {log.created_at.strftime('%b %d, %H:%M')}"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Action:** {log.action}")
                            st.write(f"**Resource:** {log.resource_type} (ID: {log.resource_id})")
                            if log.description:
                                st.write(f"**Description:** {log.description}")
                        
                        with col2:
                            if log.user_id:
                                actor = get_user_by_id(log.user_id)
                                st.write(f"**By:** {actor.name if actor else 'Unknown'}")
                            st.write(f"**When:** {log.created_at.strftime('%B %d, %Y %H:%M:%S')}")
        
        except Exception as e:
            st.error(f"❌ Error loading audit logs: {str(e)}")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    <p>🏢 <strong>Organization Management</strong> | Multi-tenant workstation configuration</p>
    <p>Phase 1.5: Full CRUD • Member management • Audit logging</p>
</div>
""", unsafe_allow_html=True)