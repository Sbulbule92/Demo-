SELECT 
    COALESCE(SUM(DurationMinutes), 0) AS TotalDurationMinutes
FROM DowntimeLog
WHERE 
    DurationMinutes > 0
    AND DurationMinutes IS NOT NULL
    AND (:ShiftID IS NULL OR :ShiftID = '' OR ShiftID = :ShiftID)
    AND (:MachineID IS NULL OR MachineID = :MachineID)
    AND CONVERT(DATE, StartTime) = 
        CASE 
            WHEN :ShiftID = 3 THEN DATEADD(DAY, 1, CONVERT(DATE, :Day))
            ELSE CONVERT(DATE, :Day)
        END;


