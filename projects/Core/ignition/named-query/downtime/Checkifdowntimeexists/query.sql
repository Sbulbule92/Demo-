SELECT 
CASE 
    WHEN EXISTS (
        SELECT 1
        FROM tbl_DowntimeLog
        WHERE MachineID = :MachineID
          AND StartTime < :EndTime
          AND ISNULL(EndTime, :StartTime) > :StartTime
    )
    THEN 1
    ELSE 0
END AS IsOverlap;