WITH Days AS (
    SELECT CAST(CAST(:startDate AS DATE) AS DATETIME) AS DayStart
    UNION ALL
    SELECT DATEADD(DAY, 1, DayStart) FROM Days
    WHERE DATEADD(DAY, 1, DayStart) < :endDate
)
SELECT
    CAST(d.DayStart AS DATE) AS [Day],
    dl.CategoryID,
    SUM(CASE WHEN x.ClipEnd > x.ClipStart
             THEN DATEDIFF(SECOND, x.ClipStart, x.ClipEnd) / 60.0
             ELSE 0 END)     AS TotalMinutes
FROM Days d
CROSS APPLY (SELECT
        CASE WHEN d.DayStart > :startDate THEN d.DayStart ELSE :startDate END AS WStart,
        CASE WHEN DATEADD(DAY, 1, d.DayStart) < :endDate
             THEN DATEADD(DAY, 1, d.DayStart) ELSE :endDate END               AS WEnd) w
JOIN dbo.tbl_DowntimeLog dl
  ON  dl.MachineID = :machineId
  AND dl.StartTime < w.WEnd
  AND (:shiftId = 0 OR dl.ShiftID = :shiftId)
CROSS APPLY (SELECT
        CASE WHEN dl.EndTime IS NOT NULL THEN dl.EndTime
             WHEN GETDATE() < w.WEnd      THEN GETDATE()
             ELSE w.WEnd END AS EffEnd) e
CROSS APPLY (SELECT
        CASE WHEN dl.StartTime > w.WStart THEN dl.StartTime ELSE w.WStart END AS ClipStart,
        CASE WHEN e.EffEnd     < w.WEnd   THEN e.EffEnd     ELSE w.WEnd   END AS ClipEnd) x
WHERE e.EffEnd > w.WStart
GROUP BY CAST(d.DayStart AS DATE), dl.CategoryID
ORDER BY [Day]
OPTION (MAXRECURSION 1100);