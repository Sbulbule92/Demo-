SELECT Top(20)[LogID]
      ,[ReasonID]
      ,[DurationMinutes]
      ,[StartTime]
      ,[EndTime]
      ,[Remarks]
      ,[UserName]
FROM DowntimeLog
WHERE DurationMinutes is Not Null
  AND CONVERT(DATE, StartTime) = CONVERT(DATE, :Day)
	AND (:ShiftID IS NULL OR ShiftID = :ShiftID)
    AND (:MachineID IS NULL OR MachineID = :MachineID)
ORDER By DurationMinutes Desc;