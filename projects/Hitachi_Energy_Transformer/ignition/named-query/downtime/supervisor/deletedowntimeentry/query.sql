-- Replace 123 with the actual LogID you want to delete
DELETE FROM dbo.tbl_DowntimeLog
WHERE LogID = :logID;
