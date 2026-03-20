UPDATE tbl_DowntimeLog
SET ReasonID = :ReasonID,Remarks= :remark, UserName = :User
WHERE LogID = :logID;
