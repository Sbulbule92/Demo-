UPDATE tbl_DowntimeLog
SET EndTime =  :EndTime,
	DowntimeStatus =  :DowntimeStatus, 
	Remarks =  :Remarks,
	MachineID =  :MachineID 
output inserted.LogID
WHERE
	LogID =  :LogID 