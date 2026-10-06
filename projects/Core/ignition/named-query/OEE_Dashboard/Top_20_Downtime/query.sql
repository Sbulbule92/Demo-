SELECT Top(20)d.[LogID]
      ,d.[ReasonID]
      ,DATEDIFF(
        MINUTE,
        IIF(d.StartTime > :StartTime, d.StartTime, :StartTime),
        IIF(d.EndTime   < :EndTime,   d.EndTime,   :EndTime)
    ) AS Duration
      ,d.[StartTime]
      ,d.[EndTime]
      ,d.[Remarks]
      ,r.ReasonName
      ,d.[UserName]
FROM tbl_DowntimeLog as d
JOIN tbl_DowntimeReason as r
ON r.ReasonID = d.ReasonID
WHERE DurationMinutes is Not Null and
  StartTime> :StartTime And EndTime <  :EndTime and MachineID =  :MachineID 
ORDER By DurationMinutes Desc;