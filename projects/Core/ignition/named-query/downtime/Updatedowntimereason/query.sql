UPDATE tbl_DowntimeLog
SET ReasonID = :ReasonID,
	Remarks= :remark,
	CategoryID =1,
	UserName = :user 
WHERE LogID = :logID;