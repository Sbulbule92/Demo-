-- ✅ Insert ONLY if no active downtime exists
INSERT INTO tbl_DowntimeLog
(
    ShiftID,
    LineID,
    MachineID,
    ReasonID,
    StartTime,
    DowntimeStatus,
    CategoryID,
    UserName,
    DowntimeSource,
    Remarks
)
OUTPUT INSERTED.LogID
Values (
	:ShiftID,
    :LineID,
    :MachineID,
    :ReasonID,
    :StartTime,
    :DowntimeStatus,
    :categoryID,
    :username,
    :DowntimeSource,
    :Remarks
);
