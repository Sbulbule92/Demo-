UPDATE tbl_DowntimeLog
SET EndTime = :EndTime
WHERE LogID = :LogID;
