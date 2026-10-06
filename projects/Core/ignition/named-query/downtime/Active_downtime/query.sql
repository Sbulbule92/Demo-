Select TOP (1) [LogID],[StartTime],[EndTime],[ReasonID],[DowntimeSource],[Remarks] from tbl_DowntimeLog
WHERE EndTime is null and MachineID =:MachineID 