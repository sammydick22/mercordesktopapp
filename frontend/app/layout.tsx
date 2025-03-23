import type React from "react"
import { Inter } from "next/font/google"
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

const inter = Inter({ subsets: ["latin"] })

export const metadata = {
  title: "TimeTracker Desktop",
  description: "Track your time efficiently across projects and tasks",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <body className={`${inter.className} bg-[#050A18]`}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} disableTransitionOnChange>
          <AuthProvider>
            <TimeTrackingProvider>
              <SyncProvider>
                <ProjectsProvider>
                  <ClientsProvider>
                    <SettingsProvider>
                      <div className="flex h-screen overflow-hidden bg-[#050A18]">
                        <Sidebar />
                        <div className="flex flex-col flex-1 overflow-hidden">
                          <Header />
                          <main className="flex-1 overflow-auto p-6 bg-[#050A18]">{children}</main>
                        </div>
                      </div>
                    </SettingsProvider>
                  </ClientsProvider>
                </ProjectsProvider>
              </SyncProvider>
            </TimeTrackingProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}



import './globals.css'