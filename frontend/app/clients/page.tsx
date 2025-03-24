"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/auth-context"
import { useClients } from "@/context/clients-context"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Users, Plus, Search, Edit, Trash2, MoreHorizontal, RefreshCw, Mail, Phone, X } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

// React component to define DialogContent
import * as React from "react"
import * as DialogPrimitive from "@radix-ui/react-dialog"

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

export default function ClientsPage() {
  const { user, loading: authLoading } = useAuth()
  const {
    clients,
    activeClients,
    loading: clientsLoading,
    error,
    fetchClients,
    createClient,
    updateClient: updateClientContext,
    deleteClient: deleteClientContext,
  } = useClients()
  const [searchQuery, setSearchQuery] = useState("")
  const [showAddClient, setShowAddClient] = useState(false)
  const [newClient, setNewClient] = useState({
    name: "",
    contact_name: "",
    email: "",
    phone: "",
    address: "",
    notes: "",
  })
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login")
    }
  }, [user, authLoading, router])

  const filteredClients = clients.filter(
    (client) =>
      client.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (client.contact_name && client.contact_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (client.email && client.email.toLowerCase().includes(searchQuery.toLowerCase())),
  )

  // Use a custom dialog open handler with setTimeout to ensure the DOM is ready
  const handleOpenDialog = () => {
    // Force the action to occur on the next event loop tick
    setTimeout(() => {
      setShowAddClient(true)
    }, 10) // Increase timeout slightly
  }

  const handleCreateClient = useCallback(async () => {
    try {
      await createClient(newClient)
      setShowAddClient(false)
      setNewClient({
        name: "",
        contact_name: "",
        email: "",
        phone: "",
        address: "",
        notes: "",
      })
      
      // Add a slight delay before fetching clients to ensure database has completed the operation
      setTimeout(() => {
        fetchClients()
      }, 500)
    } catch (err) {
      console.error("Error creating client:", err)
    }
  }, [createClient, newClient, fetchClients])

  const handleArchiveClient = useCallback(
    async (clientId: string) => {
      try {
        await updateClientContext(clientId, { is_active: false })
        fetchClients()
      } catch (err) {
        console.error("Error archiving client:", err)
      }
    },
    [updateClientContext, fetchClients],
  )

  const handleDeleteClient = useCallback(
    async (clientId: string) => {
      try {
        await deleteClientContext(clientId)
        fetchClients()
      } catch (err) {
        console.error("Error deleting client:", err)
      }
    },
    [deleteClientContext, fetchClients],
  )

  if (authLoading || !user) {
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
          Clients
        </h1>
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search clients..."
              className="pl-10 bg-[#1E293B] border-[#2D3748] text-white w-[250px]"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <Dialog open={showAddClient} onOpenChange={setShowAddClient}>
            <Button 
              onClick={handleOpenDialog}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5"
            >
              <Plus className="mr-2 h-4 w-4" />
              New Client
            </Button>
            <SimpleDialogContent className="bg-[#0F172A] border-[#1E293B] text-white" style={{ pointerEvents: "auto" }}>
              <DialogHeader>
                <DialogTitle>Create New Client</DialogTitle>
                <DialogDescription className="text-gray-400">Add a new client to your account.</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Client Name</Label>
                  <Input
                    id="name"
                    placeholder="Enter client name"
                    className="bg-[#1E293B] border-[#2D3748] text-white"
                    value={newClient.name}
                    onChange={(e) => setNewClient({ ...newClient, name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="contact_name">Contact Person</Label>
                  <Input
                    id="contact_name"
                    placeholder="Contact person name"
                    className="bg-[#1E293B] border-[#2D3748] text-white"
                    value={newClient.contact_name}
                    onChange={(e) => setNewClient({ ...newClient, contact_name: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="Email address"
                      className="bg-[#1E293B] border-[#2D3748] text-white"
                      value={newClient.email}
                      onChange={(e) => setNewClient({ ...newClient, email: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone</Label>
                    <Input
                      id="phone"
                      placeholder="Phone number"
                      className="bg-[#1E293B] border-[#2D3748] text-white"
                      value={newClient.phone}
                      onChange={(e) => setNewClient({ ...newClient, phone: e.target.value })}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="address">Address</Label>
                  <Input
                    id="address"
                    placeholder="Client address"
                    className="bg-[#1E293B] border-[#2D3748] text-white"
                    value={newClient.address}
                    onChange={(e) => setNewClient({ ...newClient, address: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="notes">Notes</Label>
                  <Textarea
                    id="notes"
                    placeholder="Additional notes"
                    className="bg-[#1E293B] border-[#2D3748] text-white resize-none"
                    value={newClient.notes}
                    onChange={(e) => setNewClient({ ...newClient, notes: e.target.value })}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setShowAddClient(false)}
                  className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateClient}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                  disabled={!newClient.name}
                >
                  Create Client
                </Button>
              </DialogFooter>
            </SimpleDialogContent>
          </Dialog>
        </div>
      </motion.div>

      <Tabs defaultValue="all" className="relative">
        <TabsList className="inline-flex h-10 items-center justify-center rounded-lg bg-[#1E293B] p-1 text-gray-400">
          <TabsTrigger
            value="all"
            className="inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-[#0F172A] data-[state=active]:text-white data-[state=active]:shadow-sm"
          >
            All Clients
          </TabsTrigger>
          <TabsTrigger
            value="active"
            className="inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-[#0F172A] data-[state=active]:text-white data-[state=active]:shadow-sm"
          >
            Active Clients
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-4">
          <ClientsTable clients={filteredClients} onArchive={handleArchiveClient} onDelete={handleDeleteClient} />
        </TabsContent>

        <TabsContent value="active" className="mt-4">
          <ClientsTable
            clients={filteredClients.filter((c) => c.is_active)}
            onArchive={handleArchiveClient}
            onDelete={handleDeleteClient}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function ClientsTable({
  clients,
  onArchive,
  onDelete,
}: {
  clients: any[]
  onArchive: (id: string) => void
  onDelete: (id: string) => void
}) {
  // Get reference to parent component's handleOpenDialog function
  const parentHandleOpenDialog = () => {
    setTimeout(() => {
      // Since this is in a different component, we indirectly trigger
      // the dialog by setting showAddClient in the parent component
      const newClientBtn = document.querySelector('button[aria-haspopup="dialog"]');
      if (newClientBtn) {
        (newClientBtn as HTMLButtonElement).click();
      }
    }, 10);
  };
  if (clients.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <div className="flex flex-col items-center gap-3">
          <Users className="h-12 w-12 text-gray-500/50" />
          <p>No clients found</p>
          <Button 
            onClick={parentHandleOpenDialog}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium rounded-full px-6 py-2.5 mt-2"
          >
            <Plus className="mr-2 h-4 w-4" />
            Create Client
          </Button>
        </div>
      </div>
    )
  }

  return (
    <Card className="bg-[#0F172A] border-[#1E293B] rounded-2xl overflow-hidden shadow-xl">
      <CardContent className="p-0">
        <Table>
          <TableHeader className="bg-[#1E293B]">
            <TableRow className="hover:bg-[#1E293B]/50 border-[#2D3748]">
              <TableHead className="text-gray-300 font-medium">Name</TableHead>
              <TableHead className="text-gray-300 font-medium">Contact</TableHead>
              <TableHead className="text-gray-300 font-medium">Email</TableHead>
              <TableHead className="text-gray-300 font-medium">Phone</TableHead>
              <TableHead className="text-gray-300 font-medium">Status</TableHead>
              <TableHead className="text-gray-300 font-medium w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {clients.map((client) => (
              <TableRow key={client.id} className="hover:bg-[#1E293B]/50 border-[#2D3748]">
                <TableCell className="font-medium text-white">{client.name}</TableCell>
                <TableCell className="text-gray-300">{client.contact_name || "—"}</TableCell>
                <TableCell className="text-gray-300">
                  {client.email ? (
                    <div className="flex items-center gap-1">
                      <Mail className="h-3 w-3" />
                      {client.email}
                    </div>
                  ) : (
                    "—"
                  )}
                </TableCell>
                <TableCell className="text-gray-300">
                  {client.phone ? (
                    <div className="flex items-center gap-1">
                      <Phone className="h-3 w-3" />
                      {client.phone}
                    </div>
                  ) : (
                    "—"
                  )}
                </TableCell>
                <TableCell>
                  {client.is_active ? (
                    <Badge className="bg-green-500/10 text-green-500 hover:bg-green-500/20">Active</Badge>
                  ) : (
                    <Badge className="bg-gray-500/10 text-gray-400 hover:bg-gray-500/20">Archived</Badge>
                  )}
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8 p-0 hover:bg-[#2D3748]">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="bg-[#0F172A] border-[#1E293B]">
                      <DropdownMenuItem className="hover:bg-[#1E293B] text-gray-300 hover:text-white">
                        <Edit className="mr-2 h-4 w-4" />
                        <span>Edit</span>
                      </DropdownMenuItem>
                      {client.is_active ? (
                        <DropdownMenuItem
                          className="hover:bg-[#1E293B] text-amber-400 hover:text-amber-300"
                          onClick={() => onArchive(client.id)}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          <span>Archive</span>
                        </DropdownMenuItem>
                      ) : (
                        <DropdownMenuItem
                          className="hover:bg-[#1E293B] text-red-400 hover:text-red-300"
                          onClick={() => onDelete(client.id)}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          <span>Delete</span>
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
