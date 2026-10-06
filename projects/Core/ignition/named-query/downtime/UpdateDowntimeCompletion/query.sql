UPDATE tbl_DowntimeLog
SET EndTime = :EndTime,
	DowntimeStatus = 0
WHERE LogID = :LogID;