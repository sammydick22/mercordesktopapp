import type React from "react"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import Sidebar from "@/components/sidebar"
import Header from "@/components/header"
import { AuthProvider } from "@/context/auth-context"
import { TimeTrackingProvider } from "@/context/time-tracking-context"
import { SyncProvider } from "@/context/sync-context"
import { ProjectsProvider } from "@/context/projects-context"
import { ClientsProvider } from "@/context/clients-context"
import { SettingsProvider } from "@/context/settings-context"
import { OrganizationsProvider } from "@/context/organizations-context"

export const metadata = {
  title: "TimeTracker Desktop",
  description: "Track your time efficiently across projects and tasks",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <head>
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" />
      </head>
      <body className="font-sans bg-[#050A18]">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} disableTransitionOnChange>
          <AuthProvider>
            <OrganizationsProvider>
              <SettingsProvider>
                <TimeTrackingProvider>
                  <SyncProvider>
                    <ProjectsProvider>
                      <ClientsProvider>
                        <div className="flex h-screen overflow-hidden bg-[#050A18]">
                          <Sidebar />
                          <div className="flex flex-col flex-1 overflow-hidden">
                            <Header />
                            <main className="flex-1 overflow-auto p-6 bg-[#050A18]">{children}</main>
                          </div>
                        </div>
                      </ClientsProvider>
                    </ProjectsProvider>
                  </SyncProvider>
                </TimeTrackingProvider>
              </SettingsProvider>
            </OrganizationsProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
