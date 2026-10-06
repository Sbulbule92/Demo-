SELECT
    ISNULL(r.ReasonName, 'Unknown') AS ReasonName,
    SUM(CASE WHEN x.ClipEnd > x.ClipStart
             THEN DATEDIFF(SECOND, x.ClipStart, x.ClipEnd) / 60.0
             ELSE 0 END)            AS TotalMinutes
FROM dbo.tbl_DowntimeLog dl
CROSS APPLY (SELECT
        CASE WHEN dl.EndTime IS NOT NULL THEN dl.EndTime
             WHEN GETDATE() < :endDate    THEN GETDATE()
             ELSE :endDate END AS EffEnd) e
CROSS APPLY (SELECT
        CASE WHEN dl.StartTime > :startDate THEN dl.StartTime ELSE :startDate END AS ClipStart,
        CASE WHEN e.EffEnd     < :endDate   THEN e.EffEnd     ELSE :endDate   END AS ClipEnd) x
LEFT JOIN dbo.tbl_DowntimeReason r ON r.ReasonID = dl.ReasonID
WHERE dl.MachineID = :machineId
  AND dl.StartTime < :endDate
  AND e.EffEnd     > :startDate
  AND (:shiftId = 0 OR dl.ShiftID = :shiftId)
GROUP BY ISNULL(r.ReasonName, 'Unknown')
HAVING SUM(CASE WHEN x.ClipEnd > x.ClipStart
                THEN DATEDIFF(SECOND, x.ClipStart, x.ClipEnd) / 60.0
                ELSE 0 END) > 0
ORDER BY TotalMinutes DESC;