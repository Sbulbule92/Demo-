Select TOP (1) [LogID],[StartTime],[EndTime],[DowntimeStatus] from tbl_DowntimeLog
WHERE 
ReasonID = 16
AND UserName = 'System' and MachineID =:MachineID order by StartTime desc;