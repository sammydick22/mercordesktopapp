# Organization Integration Guide

This document provides guidelines for implementing the frontend components necessary to interface with the organization management backend API.

## Overview

The organization system allows users to:
- Create and manage their organizations
- Invite team members to join their organizations
- Switch between organizations they belong to
- View organization-specific data (projects, time entries, etc.)

This functionality mirrors the Insightful API structure, making it compatible with their ecosystem while maintaining our application's independence.

## API Endpoints

The backend provides the following organization-related endpoints:

### Organization Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/organizations` | List organizations the user belongs to |
| POST | `/organizations` | Create a new organization |
| GET | `/organizations/{org_id}` | Get a specific organization's details |
| PUT | `/organizations/{org_id}` | Update an organization |
| DELETE | `/organizations/{org_id}` | Delete an organization |

### Organization Membership

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/organizations/{org_id}/members` | List members of an organization |
| POST | `/organizations/{org_id}/members` | Add a member to an organization |
| DELETE | `/organizations/{org_id}/members/{member_user_id}` | Remove a member from an organization |
| POST | `/organizations/{org_id}/invitations` | Create an invitation to join an organization |

## Data Models

### Organization

```typescript
interface Organization {
  id: string;
  name: string;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
}
```

### Organization Member

```typescript
interface OrganizationMember {
  id: string;
  org_id: string;
  user_id: string;
  role: string;  // "owner", "admin", or "member"
  created_at: string;
}
```

### Invitation (Future Implementation)

```typescript
interface OrganizationInvitation {
  id: string;
  org_id: string;
  email: string;
  role: string;
  created_by: string;
  created_at: string;
  expires_at: string;
  status: string; // "pending", "accepted", "rejected", "expired"
}
```

## Frontend Implementation Steps

To properly integrate with the organization API, the frontend needs to implement the following components:

### 1. API Client Module

Create an `organizations.ts` file in the `frontend/api` directory with functions to interact with each endpoint:

```typescript
// frontend/api/organizations.ts
import apiClient from "./client";

export const getOrganizations = (limit: number = 50, offset: number = 0) => 
  apiClient.get(`/organizations?limit=${limit}&offset=${offset}`);

export const getOrganization = (orgId: string) => 
  apiClient.get(`/organizations/${orgId}`);

export const createOrganization = (data: {
  name: string,
  settings?: Record<string, any>
}) => apiClient.post("/organizations", data);

export const updateOrganization = (orgId: string, data: {
  name?: string,
  settings?: Record<string, any>
}) => apiClient.put(`/organizations/${orgId}`, data);

export const deleteOrganization = (orgId: string) => 
  apiClient.delete(`/organizations/${orgId}`);

export const getOrganizationMembers = (orgId: string) => 
  apiClient.get(`/organizations/${orgId}/members`);

export const addOrganizationMember = (orgId: string, data: {
  user_id: string,
  role: string
}) => apiClient.post(`/organizations/${orgId}/members`, data);

export const removeOrganizationMember = (orgId: string, userId: string) => 
  apiClient.delete(`/organizations/${orgId}/members/${userId}`);

export const createOrganizationInvitation = (orgId: string, data: {
  email: string,
  role?: string
}) => apiClient.post(`/organizations/${orgId}/invitations`, data);
```

### 2. Context Provider

Create an `organizations-context.tsx` file in the `frontend/context` directory to:
- Manage organization state
- Provide hooks for components to access organization data
- Handle organization switching

```typescript
// frontend/context/organizations-context.tsx
"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import * as organizationsApi from "@/api/organizations";
import { useAuth } from "./auth-context";
import { useToast } from "@/hooks/use-toast";

interface Organization {
  id: string;
  name: string;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
}

interface OrganizationMember {
  id: string;
  org_id: string;
  user_id: string;
  role: string;
  created_at: string;
}

interface OrganizationsContextType {
  organizations: Organization[];
  currentOrganization: Organization | null;
  loading: boolean;
  error: string | null;
  fetchOrganizations: () => Promise<void>;
  createOrganization: (data: { name: string; settings?: Record<string, any> }) => Promise<Organization>;
  updateOrganization: (orgId: string, data: { name?: string; settings?: Record<string, any> }) => Promise<Organization>;
  deleteOrganization: (orgId: string) => Promise<void>;
  switchOrganization: (orgId: string) => void;
  getMembers: (orgId: string) => Promise<OrganizationMember[]>;
  addMember: (orgId: string, userId: string, role?: string) => Promise<OrganizationMember>;
  removeMember: (orgId: string, userId: string) => Promise<void>;
  inviteMember: (orgId: string, email: string, role?: string) => Promise<any>;
}

const OrganizationsContext = createContext<OrganizationsContextType | undefined>(undefined);

export function OrganizationsProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const { toast } = useToast();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch organizations when the user logs in
  useEffect(() => {
    if (user) {
      fetchOrganizations();
    } else {
      setOrganizations([]);
      setCurrentOrganization(null);
    }
  }, [user]);

  // Load saved current organization from localStorage
  useEffect(() => {
    if (organizations.length > 0) {
      const savedOrgId = localStorage.getItem('currentOrganizationId');
      if (savedOrgId) {
        const org = organizations.find(o => o.id === savedOrgId);
        if (org) {
          setCurrentOrganization(org);
        } else {
          // If saved org not found, use the first one
          setCurrentOrganization(organizations[0]);
          localStorage.setItem('currentOrganizationId', organizations[0].id);
        }
      } else {
        // If no saved org, use the first one
        setCurrentOrganization(organizations[0]);
        localStorage.setItem('currentOrganizationId', organizations[0].id);
      }
    }
  }, [organizations]);

  const fetchOrganizations = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await organizationsApi.getOrganizations();
      setOrganizations(response.data.organizations || []);
    } catch (err: any) {
      const message = err.response?.data?.detail || "Failed to fetch organizations";
      setError(message);
      toast({
        title: "Error",
        description: message,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const createOrganization = async (data: { name: string; settings?: Record<string, any> }): Promise<Organization> => {
    setLoading(true);
    setError(null);
    try {
      const response = await organizationsApi.createOrganization(data);
      const newOrg = response.data;
      
      // Update organizations list
      setOrganizations(prev => [...prev, newOrg]);
      
      toast({
        title: "Success",
        description: `Organization "${newOrg.name}" created successfully`,
      });
      
      return newOrg;
    } catch (err: any) {
      const message = err.response?.data?.detail || "Failed to create organization";
      setError(message);
      toast({
        title: "Error",
        description: message,
        variant: "destructive"
      });
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateOrganization = async (
    orgId: string, 
    data: { name?: string; settings?: Record<string, any> }
  ): Promise<Organization> => {
    setLoading(true);
    setError(null);
    try {
      const response = await organizationsApi.updateOrganization(orgId, data);
      const updatedOrg = response.data;
      
      // Update organizations list
      setOrganizations(prev => 
        prev.map(org => org.id === orgId ? updatedOrg : org)
      );
      
      // Update current organization if needed
      if (currentOrganization?.id === orgId) {
        setCurrentOrganization(updatedOrg);
      }
      
      toast({
        title: "Success",
        description: `Organization updated successfully`,
      });
      
      return updatedOrg;
    } catch (err: any) {
      const message = err.response?.data?.detail || "Failed to update organization";
      setError(message);
      toast({
        title: "Error",
        description: message,
        variant: "destructive"
      });
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteOrganization = async (orgId: string): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      await organizationsApi.deleteOrganization(orgId);
      
      // Remove from organizations list
      const updatedOrgs = organizations.filter(org => org.id !== orgId);
      setOrganizations(updatedOrgs);
      
      // Update current organization if needed
      if (currentOrganization?.id === orgId) {
        if (updatedOrgs.length > 0) {
          setCurrentOrganization(updatedOrgs[0]);
          localStorage.setItem('currentOrganizationId', updatedOrgs[0].id);
        } else {
          setCurrentOrganization(null);
          localStorage.removeItem('currentOrganizationId');
        }
      }
      
      toast({
        title: "Success",
        description: `Organization deleted successfully`,
      });
    } catch (err: any) {
      const message = err.response?.data?.detail || "Failed to delete organization";
      setError(message);
      toast({
        title: "Error",
        description: message,
        variant: "destructive"
      });
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const switchOrganization = (orgId: string) => {
    const org = organizations.find(o => o.id === orgId);
    if (org) {
      setCurrentOrganization(org);
      localStorage.setItem('currentOrganizationId', orgId);
      
      toast({
        title: "Organization Switched",
        description: `You are now working in "${org.name}"`,
      });
    }
  };

  const getMembers = async (orgId: string): Promise<OrganizationMember[]> => {
    try {
      const response = await organizationsApi.getOrganizationMembers(orgId);
      return response.data.members || [];
    } catch (err: any) {
      const message = err.response?.data?.detail || "Failed to fetch members";
      toast({
        title: "Error",
        description: message,
        variant: "destructive"
      });
      throw err;
    }
  };

  const addMember = async (
    orgId: string, 
    userId: string, 
    role: string = "member"
  ): Promise<OrganizationMember> => {
    try {
      const response = await organizationsApi.addOrganizationMember(orgId, { user_id: userId, role });
      
      toast({
        title: "Success",
        description: `Member added successfully`,
      });
      
      return response.data;
    } catch (err: any) {
      const message = err.response?.data?.detail || "Failed to add member";
      toast({
        title: "Error",
        description: message,
        variant: "destructive"
      });
      throw err;
    }
  };

  const removeMember = async (orgId: string, userId: string): Promise<void> => {
    try {
      await organizationsApi.removeOrganizationMember(orgId, userId);
      
      toast({
        title: "Success",
        description: `Member removed successfully`,
      });
    } catch (err: any) {
      const message = err.response?.data?.detail || "Failed to remove member";
      toast({
        title: "Error",
        description: message,
        variant: "destructive"
      });
      throw err;
    }
  };

  const inviteMember = async (
    orgId: string,
    email: string,
    role: string = "member"
  ): Promise<any> => {
    try {
      const response = await organizationsApi.createOrganizationInvitation(orgId, { email, role });
      
      toast({
        title: "Invitation Sent",
        description: `Invitation sent to ${email}`,
      });
      
      return response.data;
    } catch (err: any) {
      const message = err.response?.data?.detail || "Failed to send invitation";
      toast({
        title: "Error",
        description: message,
        variant: "destructive"
      });
      throw err;
    }
  };

  return (
    <OrganizationsContext.Provider
      value={{
        organizations,
        currentOrganization,
        loading,
        error,
        fetchOrganizations,
        createOrganization,
        updateOrganization,
        deleteOrganization,
        switchOrganization,
        getMembers,
        addMember,
        removeMember,
        inviteMember,
      }}
    >
      {children}
    </OrganizationsContext.Provider>
  );
}

export function useOrganizations() {
  const context = useContext(OrganizationsContext);
  if (context === undefined) {
    throw new Error("useOrganizations must be used within an OrganizationsProvider");
  }
  return context;
}
```

### 3. Update App Layout

Add the OrganizationsProvider to your app layout:

```tsx
// frontend/app/layout.tsx
// ...other imports
import { OrganizationsProvider } from "@/context/organizations-context";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ThemeProvider>
          <AuthProvider>
            <OrganizationsProvider>
              {/* Other providers */}
              {children}
            </OrganizationsProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

## Required UI Components

### 1. Organization Switcher

Add an organization dropdown in the header to switch between organizations:

```tsx
// components/organization-switcher.tsx
"use client";

import { useState } from "react";
import { useOrganizations } from "@/context/organizations-context";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { PlusCircle, CheckCircle, Building, ChevronDown } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";

export function OrganizationSwitcher() {
  const { organizations, currentOrganization, switchOrganization, createOrganization } = useOrganizations();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newOrgName, setNewOrgName] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;
    
    setIsCreating(true);
    try {
      const newOrg = await createOrganization({ name: newOrgName });
      switchOrganization(newOrg.id);
      setCreateDialogOpen(false);
      setNewOrgName("");
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="flex items-center gap-2">
            <Building className="h-4 w-4" />
            {currentOrganization?.name || "Select Organization"}
            <ChevronDown className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuLabel>Organizations</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {organizations.map((org) => (
            <DropdownMenuItem
              key={org.id}
              onClick={() => switchOrganization(org.id)}
              className="flex items-center gap-2"
            >
              {org.id === currentOrganization?.id && (
                <CheckCircle className="h-4 w-4 text-green-500" />
              )}
              {org.name}
            </DropdownMenuItem>
          ))}
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setCreateDialogOpen(true)}>
            <PlusCircle className="h-4 w-4 mr-2" />
            Create Organization
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Organization</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateOrg}>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <Label htmlFor="name">Organization Name</Label>
                <Input
                  id="name"
                  placeholder="My Organization"
                  value={newOrgName}
                  onChange={(e) => setNewOrgName(e.target.value)}
                  required
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setCreateDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isCreating}>
                {isCreating ? "Creating..." : "Create Organization"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
```

### 2. Organizations Page

Create a dedicated page for managing organizations:

```tsx
// app/organizations/page.tsx
"use client";

import { useState } from "react";
import { useOrganizations } from "@/context/organizations-context";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { PlusCircle, Trash, Pencil, Users, Settings } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Link from "next/link";

export default function OrganizationsPage() {
  const { organizations, createOrganization, deleteOrganization, updateOrganization, loading } = useOrganizations();
  const { toast } = useToast();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [orgName, setOrgName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const selectedOrg = selectedOrgId 
    ? organizations.find(org => org.id === selectedOrgId) 
    : null;

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orgName.trim()) return;
    
    setIsSubmitting(true);
    try {
      await createOrganization({ name: orgName });
      setCreateDialogOpen(false);
      setOrgName("");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrgId || !orgName.trim()) return;
    
    setIsSubmitting(true);
    try {
      await updateOrganization(selectedOrgId, { name: orgName });
      setEditDialogOpen(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!selectedOrgId) return;
    
    setIsSubmitting(true);
    try {
      await deleteOrganization(selectedOrgId);
      setDeleteDialogOpen(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const openEditDialog = (org: any) => {
    setSelectedOrgId(org.id);
    setOrgName(org.name);
    setEditDialogOpen(true);
  };

  const openDeleteDialog = (orgId: string) => {
    setSelectedOrgId(orgId);
    setDeleteDialogOpen(true);
  };

  return (
    <div className="container py-10">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Organizations</h1>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <PlusCircle className="mr-2 h-4 w-4" />
          Create Organization
        </Button>
      </div>

      {organizations.length === 0 ? (
        <div className="text-center py-10">
          <p className="text-muted-foreground mb-4">You don't have any organizations yet.</p>
          <Button onClick={() => setCreateDialogOpen(true)}>
            Create Your First Organization
          </Button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {organizations.map((org) => (
            <Card key={org.id}>
              <CardHeader>
                <CardTitle>{org.name}</CardTitle>
                <CardDescription>
                  Created {new Date(org.created_at).toLocaleDateString()}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  <Link href={`/organizations/${org.id}/members`} className="text-blue-500 hover:underline">
                    Manage Members
                  </Link>
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline" size="sm" onClick={() => openEditDialog(org)}>
                  <Pencil className="h-4 w-4 mr-2" />
                  Edit
                </Button>
                <Button variant="destructive" size="sm" onClick={() => openDeleteDialog(org.id)}>
                  <Trash className="h-4 w-4 mr-2" />
                  Delete
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Create Organization Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Organization</DialogTitle>
            <DialogDescription>
              Add a new organization to manage projects and time tracking.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateSubmit}>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <Label htmlFor="create-org-name">Organization Name</Label>
                <Input
                  id="create-org-name"
                  placeholder="My Organization"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  required
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setCreateDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Creating..." : "Create Organization"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Organization Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Organization</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleEditSubmit}>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <Label htmlFor="edit-org-name">Organization Name</Label>
                <Input
                  id="edit-org-name"
                  placeholder="Organization Name"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  required
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setEditDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Saving..." : "Save Changes"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Organization Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Organization</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this organization? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={isSubmitting}
            >
              {isSubmitting ? "Deleting..." : "Delete Organization"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
```

### 3. Organization Members Page

Create a page for managing organization members:

```tsx
// app/organizations/[id]/members/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useOrganizations } from "@/context/organizations-context";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PlusCircle, Trash, ArrowLeft, UserPlus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function OrganizationMembersPage() {
  const params = useParams();
  const router = useRouter();
  const orgId = params.id as string;
  const { organizations, getMembers, addMember, removeMember, inviteMember } = useOrganizations();
  const { toast } = useToast();
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("member");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Get organization details
  const organization = organizations.find(org => org.id === orgId);

  useEffect(() => {
    if (!organization) {
      toast({
        title: "Error",
        description: "Organization not found",
        variant: "destructive"
      });
      router.push("/organizations");
      return;
    }

    // Load members
    const loadMembers = async () => {
      setLoading(true);
      try {
        const data = await getMembers(orgId);
        setMembers(data);
      } catch (error) {
        // Error handling done in context
      } finally {
        setLoading(false);
      }
    };

    loadMembers();
  }, [orgId, organization, getMembers, router, toast]);

  const handleInviteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    
    set
