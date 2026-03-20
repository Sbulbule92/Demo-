INSERT INTO tbl_DowntimeLog
(
    ShiftID,
    LineID,
    MachineID,
    CategoryID,
    ReasonID,
    StartTime,
    EndTime,
    DowntimeStatus,
    Remarks,
  UserName  
)
OUTPUT INSERTED.CategoryID
VALUES
(
    1,
    1,
    1,
    :CategoryID,
    :ReasonID,
    :StartTime,
    :EndTime,
    :DowntimeStatus,
    :Remarks,
    :username
);

