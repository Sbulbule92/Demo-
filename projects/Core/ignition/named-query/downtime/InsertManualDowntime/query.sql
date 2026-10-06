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
  UserName,
  DowntimeSource
)
OUTPUT INSERTED.LogID
VALUES
(
    :shiftID,
    :lineID,
    :machineID,
    1,
    :ReasonID,
    :StartTime,
    :EndTime,
    :DowntimeStatus,
    :Remarks,
    :username,
    :DowntimeSource
    
);