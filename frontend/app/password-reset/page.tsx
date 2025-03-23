"use client"

import type React from "react"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle, Clock, Lock, Eye, EyeOff, ArrowLeft } from "lucide-react"
import { motion } from "framer-motion"

export default function PasswordResetPage() {
  const searchParams = useSearchParams()
  const token = searchParams.get("token")
  const email = searchParams.get("email")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (password !== confirmPassword) {
      setError("Passwords do not match")
      return
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long")
      return
    }

    setLoading(true)
    try {
      // This would be the actual API call to reset the password
      // await resetPasswordWithToken(email, token, password)

      // For now, we'll just simulate success
      setTimeout(() => {
        setSuccess(true)
        setLoading(false)
      }, 1000)
    } catch (err: any) {
      setError(err.message || "Failed to reset password")
      setLoading(false)
    }
  }

  const handleBackToLogin = () => {
    router.push("/login")
  }

  return (
    <div className="flex min-h-screen bg-[#050A18] items-center justify-center">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,hsl(var(--brand-gradient-start)),transparent_40%)]"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,hsl(var(--brand-gradient-end)),transparent_40%)]"></div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md px-4"
      >
        <Card className="bg-[#0F172A]/80 backdrop-blur-sm border-[#1E293B] shadow-xl">
          <CardHeader className="space-y-1 text-center">
            <div className="flex justify-center mb-2">
              <div className="rounded-full bg-blue-600 p-3">
                <Clock className="h-6 w-6 text-white" />
              </div>
            </div>
            <CardTitle className="text-2xl font-bold text-white">Reset Password</CardTitle>
            <CardDescription className="text-gray-400">
              {success ? "Your password has been reset successfully" : "Enter your new password below"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4 bg-red-900/20 border-red-800 text-red-200">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {success ? (
              <div className="text-center py-4">
                <div className="bg-green-500/10 text-green-500 p-4 rounded-lg mb-4">
                  Your password has been reset successfully. You can now log in with your new password.
                </div>
                <Button
                  onClick={handleBackToLogin}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white w-full"
                >
                  Back to Login
                </Button>
              </div>
            ) : (
              <form onSubmit={handleResetPassword} className="space-y-4">
                {!token && (
                  <Alert className="bg-amber-500/10 border-amber-500/20 text-amber-500">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Invalid or expired reset token. Please request a new password reset link.
                    </AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm text-gray-400">
                    New Password
                  </Label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Lock className="h-5 w-5 text-gray-500" />
                    </div>
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      disabled={!token || loading}
                      className="pl-10 bg-[#1E293B] border-[#2D3748] text-white"
                    />
                    <div
                      className="absolute inset-y-0 right-0 pr-3 flex items-center cursor-pointer"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? (
                        <EyeOff className="h-5 w-5 text-gray-500 hover:text-gray-400" />
                      ) : (
                        <Eye className="h-5 w-5 text-gray-500 hover:text-gray-400" />
                      )}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm_password" className="text-sm text-gray-400">
                    Confirm New Password
                  </Label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Lock className="h-5 w-5 text-gray-500" />
                    </div>
                    <Input
                      id="confirm_password"
                      type={showPassword ? "text" : "password"}
                      placeholder="••••••••"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      disabled={!token || loading}
                      className="pl-10 bg-[#1E293B] border-[#2D3748] text-white"
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-2 pt-2">
                  <Button
                    type="submit"
                    className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                    disabled={!token || loading}
                  >
                    {loading ? "Resetting Password..." : "Reset Password"}
                  </Button>

                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleBackToLogin}
                    className="bg-transparent border-[#2D3748] text-white hover:bg-[#1E293B]"
                  >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to Login
                  </Button>
                </div>
              </form>
            )}
          </CardContent>
          <CardFooter className="border-t border-[#1E293B] pt-4 text-center">
            <p className="text-xs text-gray-500">TimeTracker Desktop v1.0.0</p>
          </CardFooter>
        </Card>
      </motion.div>
    </div>
  )
}

