UPDATE dbo.tbl_DowntimeLog
SET
    StartTime = :startTime,
    EndTime   = :endTime,
    ReasonID  = :reasonID,
    Remarks   = :remark
WHERE LogID = :logID;
