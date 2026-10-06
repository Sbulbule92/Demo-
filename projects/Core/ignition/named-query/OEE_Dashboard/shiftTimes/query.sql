SELECT 
    CONVERT(VARCHAR(8), StartTime, 108) AS StartTime,
    CONVERT(VARCHAR(8), EndTime, 108) AS EndTime
FROM tbl_shift
WHERE ShiftID = :shift;