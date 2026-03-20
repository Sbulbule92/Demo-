SELECT
    s.ShiftCode,
    l.LineName,

    m.MachineCode,

    dc.CategoryName,
    dr.ReasonName,

    dl.StartTime,
    dl.EndTime,
    dl.DurationMinutes,
    dl.DowntimeStatus,
    dl.Remarks,

    userName 
FROM tbl_DowntimeLog dl
JOIN tbl_Shift s
    ON dl.ShiftID = s.ShiftID
JOIN tbl_Line l
    ON dl.LineID = l.LineID
JOIN tbl_Machine m
    ON dl.MachineID = m.MachineID
JOIN tbl_DowntimeCategory dc
    ON dl.CategoryID = dc.CategoryID
JOIN tbl_DowntimeReason dr
    ON dl.ReasonID = dr.ReasonID

ORDER BY dl.StartTime DESC;