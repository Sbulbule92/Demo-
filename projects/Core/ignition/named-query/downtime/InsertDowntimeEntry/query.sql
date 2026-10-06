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
SELECT
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
WHERE NOT EXISTS (
    SELECT 1
    FROM tbl_DowntimeLog
    WHERE MachineID = :MachineID
      AND EndTime IS NULL
);