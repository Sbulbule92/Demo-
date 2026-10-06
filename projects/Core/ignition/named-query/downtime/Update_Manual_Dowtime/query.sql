UPDATE tbl_DowntimeLog
SET ReasonID = :ReasonID,
	Remarks= :remark,
	CategoryID =1,
	UserName = :user ,
	EndTime = :EndDate
WHERE LogID = :logID;