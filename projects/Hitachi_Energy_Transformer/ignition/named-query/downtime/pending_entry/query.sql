Select TOP (1) [LogID],[StartTime],[EndTime],[DowntimeStatus] from tbl_DowntimeLog
WHERE 
ReasonID = 16
AND UserName = 'System' order by StartTime desc;
 