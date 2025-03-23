import apiClient from "./client"

export const captureScreenshot = (timeEntryId?: string) =>
  apiClient.post("/screenshots/capture", { time_entry_id: timeEntryId })

export const getScreenshots = (limit = 10, offset = 0, timeEntryId?: string) =>
  apiClient.get("/screenshots", { params: { limit, offset, time_entry_id: timeEntryId } })

export const getScreenshotUrl = (screenshotId: string) =>
  `${apiClient.defaults.baseURL}/screenshots/${screenshotId}/image`

export const getScreenshotThumbnailUrl = (screenshotId: string) =>
  `${apiClient.defaults.baseURL}/screenshots/${screenshotId}/thumbnail`

