--SELECT * FROM (
    SELECT 
        IIF(SUM(d.DurationMinutes) > 0, SUM(d.DurationMinutes), 0) AS duration,
        COUNT(d.LogID)                                               AS reason_count,
        r.ReasonName
    FROM tbl_DowntimeLog AS d
    JOIN tbl_DowntimeReason AS r
        ON r.ReasonID = d.ReasonID
    WHERE 
        d.StartTime  > :StartTime 
        AND d.EndTime   < :EndTime 
        AND d.MachineID IN (
            SELECT CAST(value AS INT) 
            FROM STRING_SPLIT(:MachineID, ',')
        )
    GROUP BY 
        r.ReasonName
--) AS Result
--ORDER BY duration DESC