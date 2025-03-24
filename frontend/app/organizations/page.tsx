"use client"

import { useState, useEffect, useCallback } from "react"
import * as React from "react"
import * as DialogPrimitive from "@radix-ui/react-dialog"
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu"
import { useRouter } from "next/navigation"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/context/auth-context"
import { useOrganizations } from "@/context/organizations-context"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Building2,
  Plus,
  Search,
  Edit,
  Trash2,
  MoreHorizontal,
  RefreshCw,
  Users,
  UserPlus,
  SettingsIcon,
  CheckCircle,
  CircleIcon,
} from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { motion } from "framer-motion"
import { formatDate } from "@/lib/utils"
import { createOrganizationInvitation } from "@/api/organizations"
import { useToast } from "@/hooks/use-toast"

// Custom Dialog components with simplified animations
const SimpleDialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      "fixed inset-0 z-50 bg-black/80 opacity-100 transition-opacity",
      className
    )}
    {...props}
  />
))
SimpleDialogOverlay.displayName = "SimpleDialogOverlay"

const SimpleDialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPrimitive.Portal>
    <SimpleDialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border p-6 shadow-lg sm:rounded-lg opacity-100 transition-opacity",
        className
      )}
      style={{ transform: "translate(-50%, -50%)" }}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPrimitive.Portal>
))
SimpleDialogContent.displayName = "SimpleDialogContent"

// Complete set of custom Dropdown Menu components with simplified animations
const SimpleDropdownMenu = DropdownMenuPrimitive.Root
SimpleDropdownMenu.displayName = "SimpleDropdownMenu"

const SimpleDropdownMenuTrigger = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Trigger
    ref={ref}
    className={cn("outline-none", className)}
    {...props}
  />
))
SimpleDropdownMenuTrigger.displayName = "SimpleDropdownMenuTrigger"

const SimpleDropdownMenuContent = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
  <DropdownMenuPrimitive.Portal>
    <DropdownMenuPrimitive.Content
      ref={ref}
      sideOffset={sideOffset}
      className={cn(
        "z-50 min-w-[8rem] overflow-hidden rounded-md border p-1 shadow-md",
        className
      )}
      style={{ 
        opacity: 1,
        pointerEvents: "auto",
        transform: "translateY(0)",
        transition: "none" 
      }}
      {...props}
    />
  </DropdownMenuPrimitive.Portal>
))
SimpleDropdownMenuContent.displayName = "SimpleDropdownMenuContent"

const SimpleDropdownMenuItem = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none",
      className
    )}
    style={{ pointerEvents: "auto" }}
    {...props}
  />
))
SimpleDropdownMenuItem.displayName = "SimpleDropdownMenuItem"

export default function OrganizationsPage() {
  const { user, loading: authLoading } = useAuth()
  const { toast } = useToast()
  const {
    organizations,
    currentOrganization,
    activeOrganizationId,
    members,
    loading: orgsLoading,
    error,
    fetchOrganizations,
    createOrganization,
    updateOrganization,
    deleteOrganization,
    fetchOrganizationMembers,
    setCurrentOrganization,
    setActiveOrganization,
  } = useOrganizations()

  const [searchQuery, setSearchQuery] = useState("")
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false)
  const [membersDialogOpen, setMembersDialogOpen] = useState(false)
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false)
  const [confirmDeleteDialogOpen, setConfirmDeleteDialogOpen] = useState(false)

  const [newOrganization, setNewOrganization] = useState({
    name: "",
    settings: {},
  })

  const [editingOrganization, setEditingOrganization] = useState<{
    id: string
    name: string
    settings: Record<string, any>
  } | null>(null)

  const [invitation, setInvitation] = useState({
    email: "",
    role: "member",
  })

  const router = useRouter()

  // Handler for activating an organization
  const handleActivateOrganization = async (org: any) => {
    try {
      await setActiveOrganization(org.id)
      toast({
        title: "Organization Activated",
        description: `${org.name} is now your active organization.`,
      })
    } catch (err) {
      console.error("Error activating organization:", err)
      toast({
        title: "Activation Failed",
        description: "Unable to set active organization.",
        variant: "destructive"
      })
    }
  }

  // Simplified initial fetch - let the context handle caching/throttling
  useEffect(() => {
    console.log("Organizations page loaded");
    
    // The context itself will perform the initial fetch, no need to trigger it here
    // This prevents multiple fetches when using React StrictMode
    
    // Only set up refresh for very long sessions (once per 5 minutes)
    const refreshInterval = setInterval(() => {
      // The context logic will decide if it should actually fetch or use cached data
      // This won't trigger state updates unless needed
      fetchOrganizations();
    }, 300000); // Every 5 minutes
    
    return () => clearInterval(refreshInterval);
  }, [fetchOrganizations]) // Using fetchOrganizations is safe because it's a stable reference from context

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login")
    }
  }, [user, authLoading, router])

  const filteredOrganizations = organizations.filter((org) =>
    org.name.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  // Use a custom dialog open handler with setTimeout to ensure the DOM is ready
  const handleOpenDialog = () => {
    // Force the action to occur on the next event loop tick
    setTimeout(() => {
      setCreateDialogOpen(true)
    }, 10) // Increase timeout slightly
  }

  const handleCreateOrganization = async () => {
    try {
      await createOrganization(newOrganization)
      setCreateDialogOpen(false)
      setNewOrganization({
        name: "",
        settings: {},
      })
      
      // Add a slight delay before fetching organizations to ensure database has completed the operation
      setTimeout(() => {
        fetchOrganizations()
      }, 500)
    } catch (err) {
      console.error("Error creating organization:", err)
    }
  }

  const handleUpdateOrganization = async () => {
    if (!editingOrganization) return

    try {
      await updateOrganization(editingOrganization.id, {
        name: editingOrganization.name,
        settings: editingOrganization.settings,
      })
      setEditDialogOpen(false)
      setEditingOrganization(null)
      fetchOrganizations()
    } catch (err) {
      console.error("Error updating organization:", err)
    }
  }

  const handleDeleteOrganization = async () => {
    if (!editingOrganization) return

    try {
      await deleteOrganization(editingOrganization.id)
      setConfirmDeleteDialogOpen(false)
      setEditingOrganization(null)
      fetchOrganizations()
    } catch (err) {
      console.error("Error deleting organization:", err)
    }
  }

  const handleSendInvitation = async () => {
    if (!currentOrganization) return

    try {
      await createOrganizationInvitation(currentOrganization.id, invitation)
      setInviteDialogOpen(false)
      setInvitation({
        email: "",
        role: "member",
      })
    } catch (err) {
      console.error("Error sending invitation:", err)
    }
  }

  const openEditDialog = (org: any) => {
    setEditingOrganization({
      id: org.id,
      name: org.name,
      settings: org.settings || {},
    })
    // Force the action to occur on the next event loop tick
    setTimeout(() => {
      setEditDialogOpen(true)
    }, 10)
  }

  const openDeleteDialog = (org: any) => {
    setEditingOrganization({
      id: org.id,
      name: org.name,
      settings: org.settings || {},
    })
    // Force the action to occur on the next event loop tick
    setTimeout(() => {
      setConfirmDeleteDialogOpen(true)
    }, 10)
  }

  const openMembersDialog = (org: any) => {
    setCurrentOrganization(org)
    // Force the action to occur on the next event loop tick
    setTimeout(() => {
      setMembersDialogOpen(true)
    }, 10)
  }

  const openSettingsDialog = (org: any) => {
    setCurrentOrganization(org)
    // Force the action to occur on the next event loop tick
    setTimeout(() => {
      setSettingsDialogOpen(true)
    }, 10)
  }

  const openInviteDialog = (org: any) => {
    setCurrentOrganization(org)
    // Force the action to occur on the next event loop tick
    setTimeout(() => {
      setInviteDialogOpen(true)
    }, 10)
  }

  if (authLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-4">
          <div className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600 text-2xl font-bold">
            TimeTracker
          </div>
          <div className="animate-spin">
            <RefreshCw size={24} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <motion.div
        className="flex items-center justify-between"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <h1 className="text-3xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600">
          Organizations
        </h1>
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search organizations..."
              className="pl-10 bg-[#1E293B] border-[#2D3748] text-white w-[250px]"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <Button
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5"
            onClick={handleOpenDialog}
          >
            <Plus className="mr-2 h-4 w-4" />
            New Organization
          </Button>
        </div>
      </motion.div>

      {/* Create Organization Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <SimpleDialogContent className="bg-[#0F172A] border-[#1E293B] text-white" style={{ pointerEvents: "auto" }}>
          <DialogHeader>
            <DialogTitle>Create New Organization</DialogTitle>
            <DialogDescription className="text-gray-400">
              Create a new organization to manage teams and projects.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Organization Name</Label>
              <Input
                id="name"
                placeholder="Enter organization name"
                className="bg-[#1E293B] border-[#2D3748] text-white"
                value={newOrganization.name}
                onChange={(e) => setNewOrganization({ ...newOrganization, name: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCreateDialogOpen(false)}
              className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateOrganization}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
              disabled={!newOrganization.name}
            >
              Create Organization
            </Button>
          </DialogFooter>
        </SimpleDialogContent>
      </Dialog>

      {/* Edit Organization Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <SimpleDialogContent className="bg-[#0F172A] border-[#1E293B] text-white" style={{ pointerEvents: "auto" }}>
          <DialogHeader>
            <DialogTitle>Edit Organization</DialogTitle>
            <DialogDescription className="text-gray-400">Update organization details.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">Organization Name</Label>
              <Input
                id="edit-name"
                placeholder="Enter organization name"
                className="bg-[#1E293B] border-[#2D3748] text-white"
                value={editingOrganization?.name || ""}
                onChange={(e) => {
                  if (editingOrganization) {
                    setEditingOrganization({
                      ...editingOrganization,
                      name: e.target.value
                    });
                  }
                }}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setEditDialogOpen(false)}
              className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpdateOrganization}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
              disabled={!editingOrganization?.name}
            >
              Save Changes
            </Button>
          </DialogFooter>
        </SimpleDialogContent>
      </Dialog>

      {/* Confirm Delete Dialog */}
      <Dialog open={confirmDeleteDialogOpen} onOpenChange={setConfirmDeleteDialogOpen}>
        <SimpleDialogContent className="bg-[#0F172A] border-[#1E293B] text-white" style={{ pointerEvents: "auto" }}>
          <DialogHeader>
            <DialogTitle>Delete Organization</DialogTitle>
            <DialogDescription className="text-gray-400">
              Are you sure you want to delete this organization? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-white">
              You are about to delete <span className="font-bold">{editingOrganization?.name}</span>.
            </p>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setConfirmDeleteDialogOpen(false)}
              className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
            >
              Cancel
            </Button>
            <Button onClick={handleDeleteOrganization} className="bg-red-600 hover:bg-red-700 text-white">
              Delete Organization
            </Button>
          </DialogFooter>
        </SimpleDialogContent>
      </Dialog>

      {/* Members Dialog */}
      <Dialog open={membersDialogOpen} onOpenChange={setMembersDialogOpen}>
        <SimpleDialogContent className="bg-[#0F172A] border-[#1E293B] text-white max-w-3xl" style={{ pointerEvents: "auto" }}>
          <DialogHeader>
            <DialogTitle>Organization Members</DialogTitle>
            <DialogDescription className="text-gray-400">
              Manage members of {currentOrganization?.name}.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-white">Members ({members.length})</h3>
              <Button
                onClick={() => {
                  setMembersDialogOpen(false)
                  setInviteDialogOpen(true)
                }}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
              >
                <UserPlus className="mr-2 h-4 w-4" />
                Invite Member
              </Button>
            </div>

            {members.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <Users className="h-12 w-12 mx-auto mb-3 text-gray-500/50" />
                <p>No members found</p>
              </div>
            ) : (
              <div className="overflow-y-auto max-h-[400px]">
                <Table>
                  <TableHeader className="bg-[#1E293B]">
                    <TableRow className="hover:bg-[#1E293B]/50 border-[#2D3748]">
                      <TableHead className="text-gray-300 font-medium">User</TableHead>
                      <TableHead className="text-gray-300 font-medium">Email</TableHead>
                      <TableHead className="text-gray-300 font-medium">Role</TableHead>
                      <TableHead className="text-gray-300 font-medium">Joined</TableHead>
                      <TableHead className="text-gray-300 font-medium w-[100px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {members.map((member) => (
                      <TableRow key={member.id} className="hover:bg-[#1E293B]/50 border-[#2D3748]">
                        <TableCell className="font-medium text-white">
                          <div className="flex items-center gap-2">
                            <Avatar className="h-8 w-8 border border-[#1E293B]">
                              <AvatarImage src={member.avatar_url || `https://avatar.vercel.sh/${member.email}`} />
                              <AvatarFallback className="bg-[#1E293B]">
                                {member.name?.substring(0, 2).toUpperCase() ||
                                  member.email?.substring(0, 2).toUpperCase()}
                              </AvatarFallback>
                            </Avatar>
                            <span>{member.name || "Unknown User"}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-gray-300">{member.email}</TableCell>
                        <TableCell>
                          <Badge
                            className={
                              member.role === "owner"
                                ? "bg-purple-500/10 text-purple-500"
                                : member.role === "admin"
                                  ? "bg-blue-500/10 text-blue-500"
                                  : "bg-green-500/10 text-green-500"
                            }
                          >
                            {member.role}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-gray-300">{formatDate(member.joined_at)}</TableCell>
                        <TableCell>
                          <SimpleDropdownMenu>
                            <SimpleDropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8 p-0 hover:bg-[#2D3748]">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </SimpleDropdownMenuTrigger>
                            <SimpleDropdownMenuContent align="end" className="bg-[#0F172A] border-[#1E293B]">
                              <SimpleDropdownMenuItem className="hover:bg-[#1E293B] text-gray-300 hover:text-white">
                                <Edit className="mr-2 h-4 w-4" />
                                <span>Change Role</span>
                              </SimpleDropdownMenuItem>
                              <SimpleDropdownMenuItem className="hover:bg-[#1E293B] text-red-400 hover:text-red-300">
                                <Trash2 className="mr-2 h-4 w-4" />
                                <span>Remove</span>
                              </SimpleDropdownMenuItem>
                            </SimpleDropdownMenuContent>
                          </SimpleDropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        </SimpleDialogContent>
      </Dialog>

      {/* Invite Member Dialog */}
      <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
        <SimpleDialogContent className="bg-[#0F172A] border-[#1E293B] text-white" style={{ pointerEvents: "auto" }}>
          <DialogHeader>
            <DialogTitle>Invite Member</DialogTitle>
            <DialogDescription className="text-gray-400">
              Send an invitation to join {currentOrganization?.name}.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter email address"
                className="bg-[#1E293B] border-[#2D3748] text-white"
                value={invitation.email}
                onChange={(e) => setInvitation({ ...invitation, email: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role">Role</Label>
              <select
                id="role"
                className="w-full rounded-md bg-[#1E293B] border-[#2D3748] text-white p-2"
                value={invitation.role}
                onChange={(e) => setInvitation({ ...invitation, role: e.target.value })}
              >
                <option value="member">Member</option>
                <option value="admin">Admin</option>
              </select>
              <p className="text-xs text-gray-400">
                Members can view and work on projects. Admins can also manage organization settings.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setInviteDialogOpen(false)}
              className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSendInvitation}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
              disabled={!invitation.email}
            >
              Send Invitation
            </Button>
          </DialogFooter>
        </SimpleDialogContent>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog open={settingsDialogOpen} onOpenChange={setSettingsDialogOpen}>
        <SimpleDialogContent className="bg-[#0F172A] border-[#1E293B] text-white" style={{ pointerEvents: "auto" }}>
          <DialogHeader>
            <DialogTitle>Organization Settings</DialogTitle>
            <DialogDescription className="text-gray-400">
              Configure settings for {currentOrganization?.name}.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="org-name">Organization Name</Label>
              <Input
                id="org-name"
                placeholder="Enter organization name"
                className="bg-[#1E293B] border-[#2D3748] text-white"
                value={currentOrganization?.name || ""}
              onChange={(e) => {
                if (currentOrganization) {
                  setCurrentOrganization({
                    ...currentOrganization,
                    name: e.target.value
                  });
                }
              }}
              />
            </div>

            {/* Additional settings would go here */}
            <div className="space-y-2">
              <Label>Billing Plan</Label>
              <div className="bg-[#1E293B] p-3 rounded-md">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-medium text-white">Free Plan</p>
                    <p className="text-sm text-gray-400">Basic features for small teams</p>
                  </div>
                  <Button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white">
                    Upgrade
                  </Button>
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSettingsDialogOpen(false)}
              className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpdateOrganization}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
            >
              Save Changes
            </Button>
          </DialogFooter>
        </SimpleDialogContent>
      </Dialog>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
      >
        {orgsLoading ? (
          <div className="flex justify-center py-8">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
          </div>
        ) : organizations.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <div className="flex flex-col items-center gap-3">
              <Building2 className="h-12 w-12 text-gray-500/50" />
              <p>No organizations found</p>
              <Button
                onClick={handleOpenDialog}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5 mt-2"
              >
                <Plus className="mr-2 h-4 w-4" />
                Create Organization
              </Button>
            </div>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredOrganizations.map((org) => (
              <Card
                key={org.id}
                className={cn(
                  "bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden shadow-xl hover:shadow-2xl transition-all duration-300 hover:translate-y-[-4px]",
                  // Add a subtle highlight for the active organization
                  org.id === activeOrganizationId && "border-blue-500/50 ring-1 ring-blue-500/30"
                )}
              >
                <CardHeader className="p-6">
                  <CardTitle className="text-xl font-semibold text-white flex items-center gap-2">
                    <Building2 className="h-5 w-5 text-blue-500" />
                    {org.name}
                    {/* Add an "Active" badge if this is the active organization */}
                    {org.id === activeOrganizationId && (
                      <Badge className="ml-2 bg-blue-500/20 text-blue-400 border-blue-500/20">
                        Active
                      </Badge>
                    )}
                  </CardTitle>
                  <CardDescription className="text-gray-400 flex items-center gap-2">
                    <Users className="h-4 w-4" />
                    {org.member_count || members.length} members
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-6 pt-0">
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-gray-400">Created {formatDate(org.created_at)}</p>
                    <SimpleDropdownMenu>
                      <SimpleDropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 p-0 hover:bg-[#2D3748]">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </SimpleDropdownMenuTrigger>
                      <SimpleDropdownMenuContent align="end" className="bg-[#0F172A] border-[#1E293B]">
                        {/* Add the Activate option at the top of the dropdown */}
                        {org.id !== activeOrganizationId ? (
                          <SimpleDropdownMenuItem
                            className="hover:bg-[#1E293B] text-blue-400 hover:text-blue-300"
                            onClick={() => handleActivateOrganization(org)}
                          >
                            <CheckCircle className="mr-2 h-4 w-4" />
                            <span>Set as Active</span>
                          </SimpleDropdownMenuItem>
                        ) : (
                          <SimpleDropdownMenuItem
                            className="hover:bg-[#1E293B] text-green-400 hover:text-green-300 cursor-default"
                          >
                            <CheckCircle className="mr-2 h-4 w-4" />
                            <span>Currently Active</span>
                          </SimpleDropdownMenuItem>
                        )}
                        
                        {/* Add a separator */}
                        <div className="my-1 h-px bg-[#2D3748]" />
                        
                        <SimpleDropdownMenuItem
                          className="hover:bg-[#1E293B] text-gray-300 hover:text-white"
                          onClick={() => openMembersDialog(org)}
                        >
                          <Users className="mr-2 h-4 w-4" />
                          <span>Members</span>
                        </SimpleDropdownMenuItem>
                        <SimpleDropdownMenuItem
                          className="hover:bg-[#1E293B] text-gray-300 hover:text-white"
                          onClick={() => openInviteDialog(org)}
                        >
                          <UserPlus className="mr-2 h-4 w-4" />
                          <span>Invite</span>
                        </SimpleDropdownMenuItem>
                        <SimpleDropdownMenuItem
                          className="hover:bg-[#1E293B] text-gray-300 hover:text-white"
                          onClick={() => openSettingsDialog(org)}
                        >
                          <SettingsIcon className="mr-2 h-4 w-4" />
                          <span>Settings</span>
                        </SimpleDropdownMenuItem>
                        <SimpleDropdownMenuItem
                          className="hover:bg-[#1E293B] text-gray-300 hover:text-white"
                          onClick={() => openEditDialog(org)}
                        >
                          <Edit className="mr-2 h-4 w-4" />
                          <span>Edit</span>
                        </SimpleDropdownMenuItem>
                        <SimpleDropdownMenuItem
                          className="hover:bg-[#1E293B] text-red-400 hover:text-red-300"
                          onClick={() => openDeleteDialog(org)}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          <span>Delete</span>
                        </SimpleDropdownMenuItem>
                      </SimpleDropdownMenuContent>
                    </SimpleDropdownMenu>
                  </div>
                  <div className="mt-4 flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
                      onClick={() => openMembersDialog(org)}
                    >
                      <Users className="mr-2 h-4 w-4" />
                      Members
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
                      onClick={() => openSettingsDialog(org)}
                    >
                      <SettingsIcon className="mr-2 h-4 w-4" />
                      Settings
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  )
}
