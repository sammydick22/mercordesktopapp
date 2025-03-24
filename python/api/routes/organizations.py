"""
Organizations API routes for the Time Tracker desktop app.
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import uuid
import json

from api.dependencies import get_current_user
from services.database import DatabaseService
from services.supabase_auth import SupabaseAuthService

# Setup logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    tags=["organizations"],
    responses={404: {"description": "Not found"}},
)

# Create database service
db_service = DatabaseService()

@router.get("/organizations")
async def get_organizations(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get organizations that the current user belongs to.
    
    Args:
        limit: Maximum number of organizations to return
        offset: Offset for pagination
        
    Returns:
        List of organizations
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Get organizations the user belongs to
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Query organizations through memberships
        cursor.execute(
            '''
            SELECT o.id, o.name, o.settings, o.created_at, o.updated_at
            FROM organizations o
            JOIN org_members m ON o.id = m.org_id
            WHERE m.user_id = ?
            LIMIT ? OFFSET ?
            ''',
            (user_id, limit, offset)
        )
        
        orgs = cursor.fetchall()
        
        # Convert to list of dictionaries
        columns = ['id', 'name', 'settings', 'created_at', 'updated_at']
        organizations = []
        
        for org in orgs:
            org_dict = dict(zip(columns, org))
            # Parse settings JSON if needed
            if org_dict['settings'] and isinstance(org_dict['settings'], str):
                try:
                    org_dict['settings'] = json.loads(org_dict['settings'])
                except:
                    org_dict['settings'] = {}
            organizations.append(org_dict)
        
        return {"organizations": organizations}
        
    except Exception as e:
        logger.error(f"Error getting organizations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get organizations: {str(e)}")

@router.post("/organizations")
async def create_organization(
    organization_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new organization.
    
    Args:
        organization_data: Data for the new organization
        
    Returns:
        The created organization
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Generate new organization ID
        org_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Create organization object
        organization = {
            "id": org_id,
            "name": organization_data.get("name", "New Organization"),
            "settings": organization_data.get("settings", {}),
            "created_at": now,
            "updated_at": now
        }
        
        # Save to database
        success = db_service.save_organization_data(organization)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create organization")
        
        # Create owner membership
        membership = {
            "id": str(uuid.uuid4()),
            "org_id": org_id,
            "user_id": user_id,
            "role": "owner",
            "created_at": now
        }
        
        success = db_service.save_org_membership(membership)
        if not success:
            # Clean up the organization if membership creation fails
            conn = db_service._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM organizations WHERE id = ?", (org_id,))
            conn.commit()
            raise HTTPException(status_code=500, detail="Failed to create organization membership")
        
        # Push organization and membership to Supabase
        try:
            # Get Supabase client from auth service
            auth_service = SupabaseAuthService()
            supabase = auth_service.supabase
            
            if supabase:
                # Create organization in Supabase
                logger.info(f"Pushing organization {org_id} to Supabase")
                org_data = {
                    "id": org_id,
                    "name": organization["name"],
                    "settings": json.dumps(organization["settings"]) if isinstance(organization["settings"], dict) else organization["settings"],
                    "created_at": organization["created_at"],
                    "updated_at": organization["updated_at"]
                }
                supabase.table("organizations").insert(org_data).execute()
                
                # Create membership in Supabase
                logger.info(f"Pushing membership for user {user_id} and organization {org_id} to Supabase")
                membership_data = {
                    "id": membership["id"],
                    "org_id": org_id,
                    "user_id": user_id,
                    "role": "owner",
                    "created_at": now
                }
                supabase.table("org_members").insert(membership_data).execute()
                
                logger.info(f"Organization {org_id} pushed to Supabase successfully")
            else:
                logger.warning("Supabase client not available, skipping remote organization creation")
        except Exception as e:
            logger.error(f"Failed to push organization to Supabase: {str(e)}")
            # Continue even if Supabase push fails to maintain local functionality
        
        return {"organization": organization}
        
    except Exception as e:
        logger.error(f"Error creating organization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create organization: {str(e)}")

@router.get("/organizations/{org_id}")
async def get_organization(
    org_id: str = Path(..., description="Organization ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get an organization by ID.
    
    Args:
        org_id: Organization ID
        
    Returns:
        The organization
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Check if user belongs to organization
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''
            SELECT COUNT(*) FROM org_members
            WHERE org_id = ? AND user_id = ?
            ''',
            (org_id, user_id)
        )
        
        count = cursor.fetchone()[0]
        if count == 0:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get organization details
        cursor.execute(
            '''
            SELECT id, name, settings, created_at, updated_at
            FROM organizations
            WHERE id = ?
            ''',
            (org_id,)
        )
        
        org = cursor.fetchone()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Convert to dictionary
        columns = ['id', 'name', 'settings', 'created_at', 'updated_at']
        org_dict = dict(zip(columns, org))
        
        # Parse settings JSON if needed
        if org_dict['settings'] and isinstance(org_dict['settings'], str):
            try:
                org_dict['settings'] = json.loads(org_dict['settings'])
            except:
                org_dict['settings'] = {}
        
        return org_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get organization: {str(e)}")

@router.put("/organizations/{org_id}")
async def update_organization(
    org_id: str = Path(..., description="Organization ID"),
    organization_data: Dict[str, Any] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update an organization.
    
    Args:
        org_id: Organization ID
        organization_data: Data to update
        
    Returns:
        The updated organization
    """
    try:
        if organization_data is None:
            organization_data = {}
            
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Check if user belongs to organization
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''
            SELECT role FROM org_members
            WHERE org_id = ? AND user_id = ?
            ''',
            (org_id, user_id)
        )
        
        member = cursor.fetchone()
        if not member:
            raise HTTPException(status_code=403, detail="Access denied")
            
        role = member[0]
        if role != "owner" and role != "admin":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Get current organization data
        cursor.execute(
            '''
            SELECT id, name, settings, created_at, updated_at
            FROM organizations
            WHERE id = ?
            ''',
            (org_id,)
        )
        
        org = cursor.fetchone()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
            
        # Convert to dictionary
        columns = ['id', 'name', 'settings', 'created_at', 'updated_at']
        org_dict = dict(zip(columns, org))
        
        # Parse settings JSON
        settings = {}
        if org_dict['settings'] and isinstance(org_dict['settings'], str):
            try:
                settings = json.loads(org_dict['settings'])
            except:
                settings = {}
        
        # Update organization
        name = organization_data.get("name", org_dict["name"])
        updated_settings = organization_data.get("settings", settings)
        
        # Create updated organization object
        updated_org = {
            "id": org_id,
            "name": name,
            "settings": updated_settings,
            "created_at": org_dict["created_at"],
            "updated_at": datetime.now().isoformat()
        }
        
        # Save to database
        success = db_service.save_organization_data(updated_org)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update organization")
        
        # Update organization in Supabase
        try:
            # Get Supabase client from auth service
            auth_service = SupabaseAuthService()
            supabase = auth_service.supabase
            
            if supabase:
                # Update organization in Supabase
                logger.info(f"Updating organization {org_id} in Supabase")
                org_data = {
                    "name": updated_org["name"],
                    "settings": json.dumps(updated_org["settings"]) if isinstance(updated_org["settings"], dict) else updated_org["settings"],
                    "updated_at": updated_org["updated_at"]
                }
                supabase.table("organizations").update(org_data).eq("id", org_id).execute()
                logger.info(f"Organization {org_id} updated in Supabase successfully")
            else:
                logger.warning("Supabase client not available, skipping remote organization update")
        except Exception as e:
            logger.error(f"Failed to update organization in Supabase: {str(e)}")
            # Continue even if Supabase update fails to maintain local functionality
        
        return updated_org
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update organization: {str(e)}")

@router.delete("/organizations/{org_id}")
async def delete_organization(
    org_id: str = Path(..., description="Organization ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete an organization.
    
    Args:
        org_id: Organization ID
        
    Returns:
        Success message
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Check if user is the organization owner
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''
            SELECT role FROM org_members
            WHERE org_id = ? AND user_id = ?
            ''',
            (org_id, user_id)
        )
        
        member = cursor.fetchone()
        if not member or member[0] != "owner":
            raise HTTPException(status_code=403, detail="Only organization owners can delete organizations")
        
        # Get organization details for the response
        cursor.execute(
            '''
            SELECT id, name FROM organizations
            WHERE id = ?
            ''',
            (org_id,)
        )
        
        org = cursor.fetchone()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Delete organization memberships first
        cursor.execute(
            '''
            DELETE FROM org_members
            WHERE org_id = ?
            ''',
            (org_id,)
        )
        
        # Delete organization
        cursor.execute(
            '''
            DELETE FROM organizations
            WHERE id = ?
            ''',
            (org_id,)
        )
        
        conn.commit()
        
        # Delete organization and memberships from Supabase
        try:
            # Get Supabase client from auth service
            auth_service = SupabaseAuthService()
            supabase = auth_service.supabase
            
            if supabase:
                # Delete memberships in Supabase
                logger.info(f"Deleting organization memberships for org {org_id} from Supabase")
                supabase.table("org_members").delete().eq("org_id", org_id).execute()
                
                # Delete organization in Supabase
                logger.info(f"Deleting organization {org_id} from Supabase")
                supabase.table("organizations").delete().eq("id", org_id).execute()
                
                logger.info(f"Organization {org_id} and its memberships deleted from Supabase successfully")
            else:
                logger.warning("Supabase client not available, skipping remote organization deletion")
        except Exception as e:
            logger.error(f"Failed to delete organization from Supabase: {str(e)}")
            # Continue even if Supabase deletion fails to maintain local functionality
        
        return {
            "id": org[0],
            "name": org[1],
            "message": "Organization deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting organization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete organization: {str(e)}")
        
@router.post("/organizations/cleanup")
async def cleanup_orphaned_memberships(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Clean up orphaned organization memberships.
    
    This endpoint removes memberships that reference non-existent organizations.
    Useful for maintenance operations.
    
    Returns:
        Result of the cleanup operation
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Only allow cleanup for authenticated users
        logger.info(f"User {user_id} initiated cleanup of orphaned organization memberships")
        
        # Clean up orphaned memberships
        cleanup_result = db_service.cleanup_orphaned_memberships()
        
        if not cleanup_result["success"]:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to clean up orphaned memberships: {cleanup_result.get('error', 'Unknown error')}"
            )
        
        # Also check and remove memberships for a known problematic test organization ID
        problematic_org_id = "123e4567-e89b-12d3-a456-426614174000"
        logger.info(f"Removing memberships for known problematic organization ID: {problematic_org_id}")
        db_service.remove_specific_membership(problematic_org_id)
        
        return {
            "status": "success",
            "orphaned_count": cleanup_result["orphaned_count"],
            "message": f"Successfully cleaned up {cleanup_result['orphaned_count']} orphaned organization memberships"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up orphaned memberships: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clean up orphaned memberships: {str(e)}")

@router.get("/organizations/{org_id}/members")
async def get_organization_members(
    org_id: str = Path(..., description="Organization ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get members of an organization.
    
    Args:
        org_id: Organization ID
        
    Returns:
        List of organization members
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Check if user belongs to organization
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''
            SELECT COUNT(*) FROM org_members
            WHERE org_id = ? AND user_id = ?
            ''',
            (org_id, user_id)
        )
        
        count = cursor.fetchone()[0]
        if count == 0:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get organization members
        cursor.execute(
            '''
            SELECT id, org_id, user_id, role, created_at
            FROM org_members
            WHERE org_id = ?
            ''',
            (org_id,)
        )
        
        members = cursor.fetchall()
        
        # Convert to list of dictionaries
        columns = ['id', 'org_id', 'user_id', 'role', 'created_at']
        member_list = [dict(zip(columns, member)) for member in members]
        
        return {"members": member_list}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization members: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get organization members: {str(e)}")

@router.post("/organizations/{org_id}/members")
async def add_organization_member(
    org_id: str = Path(..., description="Organization ID"),
    member_data: Dict[str, Any] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Add a member to an organization.
    
    Args:
        org_id: Organization ID
        member_data: Member data including user_id and role
        
    Returns:
        The added member
    """
    try:
        if member_data is None:
            raise HTTPException(status_code=400, detail="Member data is required")
            
        if "user_id" not in member_data:
            raise HTTPException(status_code=400, detail="user_id is required")
            
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Check if user has admin permissions
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''
            SELECT role FROM org_members
            WHERE org_id = ? AND user_id = ?
            ''',
            (org_id, user_id)
        )
        
        member = cursor.fetchone()
        if not member or (member[0] != "owner" and member[0] != "admin"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Check if organization exists
        cursor.execute(
            '''
            SELECT COUNT(*) FROM organizations
            WHERE id = ?
            ''',
            (org_id,)
        )
        
        count = cursor.fetchone()[0]
        if count == 0:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Check if user is already a member
        cursor.execute(
            '''
            SELECT COUNT(*) FROM org_members
            WHERE org_id = ? AND user_id = ?
            ''',
            (org_id, member_data["user_id"])
        )
        
        count = cursor.fetchone()[0]
        if count > 0:
            raise HTTPException(status_code=400, detail="User is already a member of this organization")
        
        # Add member
        member_id = str(uuid.uuid4())
        role = member_data.get("role", "member")
        now = datetime.now().isoformat()
        
        # Create membership
        membership = {
            "id": member_id,
            "org_id": org_id,
            "user_id": member_data["user_id"],
            "role": role,
            "created_at": now
        }
        
        success = db_service.save_org_membership(membership)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add organization member")
            
        # Push membership to Supabase
        try:
            # Get Supabase client from auth service
            auth_service = SupabaseAuthService()
            supabase = auth_service.supabase
            
            if supabase:
                # Create membership in Supabase
                logger.info(f"Pushing membership for user {member_data['user_id']} and organization {org_id} to Supabase")
                membership_data = {
                    "id": member_id,
                    "org_id": org_id,
                    "user_id": member_data["user_id"],
                    "role": role,
                    "created_at": now
                }
                supabase.table("org_members").insert(membership_data).execute()
                
                logger.info(f"Membership for user {member_data['user_id']} pushed to Supabase successfully")
            else:
                logger.warning("Supabase client not available, skipping remote membership creation")
        except Exception as e:
            logger.error(f"Failed to push membership to Supabase: {str(e)}")
            # Continue even if Supabase push fails to maintain local functionality
        
        return membership
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding organization member: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add organization member: {str(e)}")

@router.delete("/organizations/{org_id}/members/{member_user_id}")
async def remove_organization_member(
    org_id: str = Path(..., description="Organization ID"),
    member_user_id: str = Path(..., description="Member user ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Remove a member from an organization.
    
    Args:
        org_id: Organization ID
        member_user_id: User ID of the member to remove
        
    Returns:
        Success message
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Check if user has admin permissions
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''
            SELECT role FROM org_members
            WHERE org_id = ? AND user_id = ?
            ''',
            (org_id, user_id)
        )
        
        member = cursor.fetchone()
        if not member or (member[0] != "owner" and member[0] != "admin" and user_id != member_user_id):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Check if member exists
        cursor.execute(
            '''
            SELECT role FROM org_members
            WHERE org_id = ? AND user_id = ?
            ''',
            (org_id, member_user_id)
        )
        
        member_to_remove = cursor.fetchone()
        if not member_to_remove:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Prevent removing the last owner
        if member_to_remove[0] == "owner":
            cursor.execute(
                '''
                SELECT COUNT(*) FROM org_members
                WHERE org_id = ? AND role = 'owner'
                ''',
                (org_id,)
            )
            
            owner_count = cursor.fetchone()[0]
            if owner_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot remove the last owner of an organization")
        
        # Remove member
        cursor.execute(
            '''
            DELETE FROM org_members
            WHERE org_id = ? AND user_id = ?
            ''',
            (org_id, member_user_id)
        )
        
        conn.commit()
        
        # Remove membership from Supabase
        try:
            # Get Supabase client from auth service
            auth_service = SupabaseAuthService()
            supabase = auth_service.supabase
            
            if supabase:
                # Delete membership in Supabase
                logger.info(f"Removing membership for user {member_user_id} and organization {org_id} from Supabase")
                supabase.table("org_members").delete().eq("org_id", org_id).eq("user_id", member_user_id).execute()
                
                logger.info(f"Membership for user {member_user_id} removed from Supabase successfully")
            else:
                logger.warning("Supabase client not available, skipping remote membership deletion")
        except Exception as e:
            logger.error(f"Failed to remove membership from Supabase: {str(e)}")
            # Continue even if Supabase deletion fails to maintain local functionality
        
        return {
            "org_id": org_id,
            "user_id": member_user_id,
            "message": "Member removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing organization member: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to remove organization member: {str(e)}")

@router.post("/organizations/{org_id}/invitations")
async def create_invitation(
    org_id: str = Path(..., description="Organization ID"),
    invitation_data: Dict[str, Any] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create an invitation to join an organization.
    
    Args:
        org_id: Organization ID
        invitation_data: Invitation data including email and role
        
    Returns:
        The created invitation
    """
    try:
        if invitation_data is None:
            raise HTTPException(status_code=400, detail="Invitation data is required")
            
        if "email" not in invitation_data:
            raise HTTPException(status_code=400, detail="email is required")
            
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Check if user has admin permissions
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''
            SELECT role FROM org_members
            WHERE org_id = ? AND user_id = ?
            ''',
            (org_id, user_id)
        )
        
        member = cursor.fetchone()
        if not member or (member[0] != "owner" and member[0] != "admin"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Check if organization exists
        cursor.execute(
            '''
            SELECT name FROM organizations
            WHERE id = ?
            ''',
            (org_id,)
        )
        
        org = cursor.fetchone()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
            
        # For now, just return a success message with the invitation details
        # In a real implementation, you would store this invitation and send an email
        
        return {
            "org_id": org_id,
            "org_name": org[0],
            "email": invitation_data["email"],
            "role": invitation_data.get("role", "member"),
            "message": "Invitation created successfully",
            "note": "In a production environment, an email would be sent to the recipient"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization invitation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create organization invitation: {str(e)}")
