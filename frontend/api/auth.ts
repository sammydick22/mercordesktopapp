import apiClient from "./client"

export const login = (email: string, password: string) => apiClient.post("/auth/login", { email, password })

export const signup = (email: string, password: string) => apiClient.post("/auth/signup", { email, password })

export const logout = () => apiClient.post("/auth/logout")

export const getCurrentUser = () => apiClient.get("/auth/user")

export const resetPassword = (email: string) => apiClient.post("/auth/reset-password", { email })

