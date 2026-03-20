SELECT Sum(DurationMinutes) as duration,
		count(8) as reason_count
      ,[Remarks] as reason
FROM DowntimeLog
WHERE CONVERT(DATE, StartTime) = CONVERT(DATE, :Day)
  AND ShiftID = :ShiftID
  AND MachineID = :MachineID
GROUP By Remarks
order by Duration desc;