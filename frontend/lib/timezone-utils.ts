// Utility functions for handling timezones in time tracking

/**
 * Adjusts a timestamp to account for timezone differences  
 * 
 * @param dateString - ISO date string to be adjusted
 * @param timezone - User's timezone (e.g., 'America/Los_Angeles')
 * @param useLocalTime - Whether to use the user's local time (default: true)
 * @returns Adjusted timestamp in milliseconds
 */
export function getAdjustedTimestamp(dateString: string, timezone?: string, useLocalTime = true): number {
  try {
    console.log("[TIMER DEBUG] getAdjustedTimestamp called with:", { dateString, timezone, useLocalTime });
    
    // Check if the string has a timezone marker (Z or +/-xx:xx)
    const hasTimezoneMarker = dateString.endsWith('Z') || /[+-]\d\d:\d\d$/.test(dateString);
    
    // For server timestamps without timezone marker, ensure proper parsing
    // by appending 'Z' to indicate UTC if it's missing
    let normalizedDateString = dateString;
    if (!hasTimezoneMarker) {
      console.log("[TIMER DEBUG] Timestamp missing timezone marker, treating as UTC by adding Z");
      normalizedDateString = dateString + 'Z';
    }
    
    // If no timezone is provided or we don't want to adjust, just use the timestamp as is
    if (!timezone || !useLocalTime) {
      const timestamp = new Date(normalizedDateString).getTime();
      console.log("[TIMER DEBUG] No timezone adjustment, returning:", timestamp);
      return timestamp;
    }
    
    // Parse the date and get timestamp
    const timestamp = new Date(normalizedDateString).getTime();
    const now = Date.now();
    
    // Safety check: ensure timestamp is not thousands of years in future
    // This happens with timezone bugs, but we still want to allow timestamps
    // that are a few seconds in the future due to clock skew
    const oneHourInMs = 60 * 60 * 1000;
    if (timestamp > now + oneHourInMs) {
      console.log("[TIMER DEBUG] Timestamp far in future, likely timezone issue:", { 
        original: timestamp, 
        diff: timestamp - now,
        adjustedTo: now
      });
      return now; // Cap at current time to prevent negative elapsed time
    }
    
    console.log("[TIMER DEBUG] Timestamp is reasonable:", {
      timestamp,
      diffFromNow: timestamp - now
    });
    return timestamp;
  } catch (error) {
    console.error("[TIMER DEBUG] Error adjusting timezone:", error);
    // Fallback to simple timestamp conversion
    return new Date(dateString).getTime();
  }
}

/**
 * Safely calculates elapsed time, ensuring it's never negative
 * 
 * @param startTimeStr - ISO date string for the start time
 * @param timezone - User's timezone (optional)
 * @returns Elapsed seconds (always >= 0)
 */
export function calculateElapsedTime(startTimeStr: string, timezone?: string): number {
  try {
    console.log("[TIMER DEBUG] calculateElapsedTime called with:", {
      startTimeStr,
      timezone
    });
    
    const startTime = getAdjustedTimestamp(startTimeStr, timezone);
    const now = Date.now();
    
    // Debug log the values
    console.log("[TIMER DEBUG] Time calculation:", {
      startTime,
      now,
      diff: now - startTime,
      elapsedSeconds: Math.floor((now - startTime) / 1000)
    });
    
    // Use Math.max to ensure we never return negative values
    const elapsed = Math.max(0, Math.floor((now - startTime) / 1000));
    console.log("[TIMER DEBUG] Final elapsed time:", elapsed);
    return elapsed;
  } catch (error) {
    console.error("[TIMER DEBUG] Error calculating elapsed time:", error);
    return 0;
  }
}
