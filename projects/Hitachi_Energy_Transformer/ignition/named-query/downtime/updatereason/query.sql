UPDATE tbl_DowntimeLog
SET ReasonID = :ReasonID,
	UserName = :User
WHERE LogID = :logID
