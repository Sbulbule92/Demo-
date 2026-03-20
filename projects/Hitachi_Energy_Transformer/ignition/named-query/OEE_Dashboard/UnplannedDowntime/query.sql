SELECT 
    CASE 
        WHEN SUM(DurationMinutes) IS NULL 
             OR SUM(DurationMinutes) <= 0
        THEN '00:00:00'
        ELSE
            RIGHT('0' + CAST(SUM(DurationMinutes) / 60 AS VARCHAR), 2) + ':' +
            RIGHT('0' + CAST(SUM(DurationMinutes) % 60 AS VARCHAR), 2) + ':00'
    END AS dt
FROM DowntimeLog
WHERE 
    DurationMinutes > 0
    AND DurationMinutes IS NOT NULL
   AND (:ShiftID IS NULL OR :ShiftID = '' OR ShiftID = :ShiftID)
    AND (:MachineID IS NULL OR MachineID = :MachineID)
    AND CONVERT(DATE, StartTime) = 
        CASE 
            WHEN :ShiftID = 3 
                THEN DATEADD(DAY, 1, CONVERT(DATE, :Day))
            ELSE 
                CONVERT(DATE, :Day)
        END;

