SELECT
    dl.LogID,
    dl.ShiftID,
    dl.StartTime,
    dl.EndTime,
    dl.DurationMinutes,
    CASE WHEN x.ClipEnd > x.ClipStart
         THEN DATEDIFF(SECOND, x.ClipStart, x.ClipEnd) / 60.0
         ELSE 0 END              AS ClippedMinutes,
    dl.CategoryID,
    c.CategoryName,
    dl.ReasonID,
    r.ReasonName,
    dl.Remarks,
    dl.UserName
FROM dbo.tbl_DowntimeLog dl
CROSS APPLY (SELECT
        CASE WHEN dl.EndTime IS NOT NULL THEN dl.EndTime
             WHEN GETDATE() < :endDate    THEN GETDATE()
             ELSE :endDate END AS EffEnd) e
CROSS APPLY (SELECT
        CASE WHEN dl.StartTime > :startDate THEN dl.StartTime ELSE :startDate END AS ClipStart,
        CASE WHEN e.EffEnd     < :endDate   THEN e.EffEnd     ELSE :endDate   END AS ClipEnd) x
LEFT JOIN dbo.tbl_DowntimeReason   r ON r.ReasonID   = dl.ReasonID
LEFT JOIN dbo.tbl_DowntimeCategory c ON c.CategoryID = dl.CategoryID
WHERE dl.MachineID = :machineId
  AND dl.StartTime < :endDate
  AND e.EffEnd     > :startDate
  AND (:shiftId = 0 OR dl.ShiftID = :shiftId)
ORDER BY dl.StartTime;