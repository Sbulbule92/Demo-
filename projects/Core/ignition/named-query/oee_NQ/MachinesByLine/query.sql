SELECT
    MachineID,
    MachineCode,
    MachineName
FROM dbo.tbl_Machine
WHERE LineID = :lineId
  AND IsActive = 1
ORDER BY MachineCode;