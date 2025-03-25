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
    
    // Get the server timestamp
    const timestamp = new Date(normalizedDateString).getTime();
    const now = Date.now();
    
    // Detect likely timezone issues: if timestamp is more than 7 hours in the future or past
    // This would indicate a timezone offset issue that needs correction
    const sevenHoursMs = 7 * 60 * 60 * 1000;
    if (Math.abs(timestamp - now) > sevenHoursMs) {
      console.log("[TIMER DEBUG] Detected likely timezone offset issue:", { 
        original: timestamp,
        now: now,
        diff: timestamp - now,
        diffHours: (timestamp - now) / (60 * 60 * 1000)
      });
      
      // Calculate the detected offset hours (roughly)
      const offsetHours = Math.round((timestamp - now) / (60 * 60 * 1000));
      
      // If offset is likely a timezone issue, correct it by adjusting the timestamp
      // For example, if timestamp is 7 hours ahead, we subtract 7 hours
      const correctedTimestamp = timestamp - (offsetHours * 60 * 60 * 1000);
      
      console.log("[TIMER DEBUG] Applied timezone correction:", {
        offsetHours,
        correctedTimestamp,
        diffFromNowAfterCorrection: correctedTimestamp - now
      });
      
      return correctedTimestamp;
    }
    
    // If timestamp is reasonable (within 7 hours), use it as is
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
