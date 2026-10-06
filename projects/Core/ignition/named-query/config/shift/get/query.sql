SELECT ShiftID, ShiftCode, ShiftName,
       CONVERT(varchar(8), StartTime, 108) AS StartTime,
       CONVERT(varchar(8), EndTime,   108) AS EndTime,
       Description, IsActive
FROM tbl_Shift ORDER BY ShiftID;