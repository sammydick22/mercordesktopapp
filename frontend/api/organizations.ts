import apiClient from "./client";

/**
 * Get organizations that the current user belongs to
 * @param limit Maximum number of organizations to return
 * @param offset Offset for pagination
 * @returns List of organizations
 */
export const getOrganizations = (limit: number = 50, offset: number = 0) => 
  apiClient.get(`/organizations?limit=${limit}&offset=${offset}`);

/**
 * Get a specific organization's details
 * @param orgId Organization ID
 * @returns Organization details
 */
export const getOrganization = (orgId: string) => 
  apiClient.get(`/organizations/${orgId}`);

/**
 * Create a new organization
 * @param data Organization data
 * @returns Created organization
 */
export const createOrganization = (data: {
  name: string,
  settings?: Record<string, any>
}) => apiClient.post("/organizations", data);

/**
 * Update an organization
 * @param orgId Organization ID
 * @param data Data to update
 * @returns Updated organization
 */
export const updateOrganization = (orgId: string, data: {
  name?: string,
  settings?: Record<string, any>
}) => apiClient.put(`/organizations/${orgId}`, data);

/**
 * Delete an organization
 * @param orgId Organization ID
 * @returns Success message
 */
export const deleteOrganization = (orgId: string) => 
  apiClient.delete(`/organizations/${orgId}`);

/**
 * Get members of an organization
 * @param orgId Organization ID
 * @returns List of organization members
 */
export const getOrganizationMembers = (orgId: string) => 
  apiClient.get(`/organizations/${orgId}/members`);

/**
 * Add a member to an organization
 * @param orgId Organization ID
 * @param data Member data
 * @returns Added member
 */
export const addOrganizationMember = (orgId: string, data: {
  user_id: string,
  role: string
}) => apiClient.post(`/organizations/${orgId}/members`, data);

/**
 * Remove a member from an organization
 * @param orgId Organization ID
 * @param userId User ID of the member to remove
 * @returns Success message
 */
export const removeOrganizationMember = (orgId: string, userId: string) => 
  apiClient.delete(`/organizations/${orgId}/members/${userId}`);

/**
 * Create an invitation to join an organization
 * @param orgId Organization ID
 * @param data Invitation data
 * @returns Created invitation
 */
export const createOrganizationInvitation = (orgId: string, data: {
  email: string,
  role?: string
}) => apiClient.post(`/organizations/${orgId}/invitations`, data);
