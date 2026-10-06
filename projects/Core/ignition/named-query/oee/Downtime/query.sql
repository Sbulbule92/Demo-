SELECT
    dl.LogID                                          AS id,
    dl.StartTime                                      AS start_time,
    dl.EndTime                                        AS end_time,
    CASE
        WHEN dl.EndTime IS NOT NULL
            THEN COALESCE(dl.DurationMinutes,
                          DATEDIFF(MINUTE, dl.StartTime, dl.EndTime))     -- closed: unchanged
        WHEN DATEDIFF(MINUTE, dl.StartTime, :fallbackEnd) < 0 THEN 0
        ELSE DATEDIFF(MINUTE, dl.StartTime, :fallbackEnd)                 -- open: end = selection end
    END                                               AS duration_min,
    dl.ReasonID                                       AS reason_id,
    r.ReasonName                                      AS reason,
    dl.Remarks                                        AS remarks,
    dl.UserName                                       AS [user]
FROM dbo.tbl_DowntimeLog dl
LEFT JOIN dbo.tbl_DowntimeReason r
       ON r.ReasonID = dl.ReasonID
WHERE dl.MachineID = :machineId
  AND dl.StartTime >= :startTime
  AND dl.StartTime <  :endTime
ORDER BY dl.StartTime;