SELECT
    r.ReasonName AS reason,
    SUM(
        CASE
            WHEN dl.EndTime IS NOT NULL
                THEN COALESCE(dl.DurationMinutes,
                              DATEDIFF(MINUTE, dl.StartTime, dl.EndTime))
            WHEN DATEDIFF(MINUTE, dl.StartTime, :fallbackEnd) < 0 THEN 0
            ELSE DATEDIFF(MINUTE, dl.StartTime, :fallbackEnd)
        END
    ) AS total_min
FROM dbo.tbl_DowntimeLog dl
LEFT JOIN dbo.tbl_DowntimeReason r
       ON r.ReasonID = dl.ReasonID
WHERE dl.MachineID = :machineId
  AND dl.StartTime >= :startTime
  AND dl.StartTime <  :endTime
GROUP BY r.ReasonName
ORDER BY total_min DESC;