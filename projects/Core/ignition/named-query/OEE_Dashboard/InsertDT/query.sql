INSERT INTO DowntimeLog(
	ShiftID,
	LineID,
	MachineID,
	CategoryID,
	ReasonID,
	StartTime,
	DowntimeStatus,
	UserName
)OUTPUT INSERTED.LogID
values( :ShiftID, :LineID, :MachineID ,  :CategoryID ,  :ReasonID ,  :StartTime , :DowntimeStatus ,  :UserName   )