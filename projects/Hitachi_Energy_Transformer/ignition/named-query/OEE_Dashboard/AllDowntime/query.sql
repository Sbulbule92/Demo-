SELECT [LogID]
      ,[ReasonID]
      ,[DurationMinutes]
      ,[StartTime]
      ,[EndTime]
      ,[Remarks]
      ,[UserName]
FROM DowntimeLog
Where ShiftID = :Shift And CONVERT(DATE, StartTime) = CONVERT(DATE, :Day)