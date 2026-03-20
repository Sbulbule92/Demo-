SELECT
    dl.LogID,
    dl.ReasonID,
    dl.Remarks,
    dl.DurationMinutes
FROM historian.dbo.DowntimeLog as dl
WHERE dl.UserName = :user
  AND CAST(dl.StartTime AS DATE) = CAST(:day AS DATE);

