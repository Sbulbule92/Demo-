INSERT INTO tbl_DowntimeLog
(
    ShiftID,
    LineID,
    MachineID,
    ReasonID,
    StartTime,
    DowntimeStatus,
 	CategoryID,
  UserName  
)

OUTPUT INSERTED.LogID
VALUES
(
    :ShiftID,
    1,
    1,
    :ReasonID,
    :StartTime,
    :DowntimeStatus,
    1,
    :username
);

