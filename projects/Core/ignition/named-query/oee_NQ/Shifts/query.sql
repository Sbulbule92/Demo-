SELECT
    ShiftID,
    ShiftCode,
    ShiftName,
    StartTime,
    EndTime
FROM dbo.tbl_Shift
WHERE IsActive = 1
ORDER BY ShiftID;