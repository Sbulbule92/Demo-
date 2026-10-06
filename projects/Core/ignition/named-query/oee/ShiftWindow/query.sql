SELECT
    s.ShiftID,
    s.ShiftName AS shift_name,
    CAST(:shiftDate AS datetime) + CAST(s.StartTime AS datetime) AS shift_start,
    CASE
        WHEN s.EndTime <= s.StartTime                       -- wraps past midnight (Night shift)
            THEN CAST(DATEADD(DAY, 1, :shiftDate) AS datetime) + CAST(s.EndTime AS datetime)
        ELSE     CAST(:shiftDate AS datetime) + CAST(s.EndTime AS datetime)
    END AS shift_end
FROM dbo.tbl_Shift s
WHERE s.ShiftID = :shiftId;