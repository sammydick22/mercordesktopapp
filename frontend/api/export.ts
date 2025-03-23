import apiClient from "./client"

export const exportTimeEntries = (params: {
  format: "csv" | "xlsx" | "pdf"
  start_date?: string
  end_date?: string
  project_id?: string
  client_id?: string
  include_screenshots?: boolean
}) =>
  apiClient.get("/export/time-entries", {
    params,
    responseType: "blob",
  })

export const exportReport = (params: {
  format: "csv" | "xlsx" | "pdf"
  report_type: "summary" | "detailed" | "client" | "project"
  start_date?: string
  end_date?: string
  project_id?: string
  client_id?: string
  group_by?: "day" | "week" | "month" | "project" | "client"
}) =>
  apiClient.get("/export/report", {
    params,
    responseType: "blob",
  })

