Update tbl_DowntimeLog
Set ReasonID   = :ReasonID,
    StartTime  = :StartTime,
    EndTime    = :EndTime,
    Remarks    = :Remarks,
    modifiedBy = :Supervisor
Where LogID    = :LogID