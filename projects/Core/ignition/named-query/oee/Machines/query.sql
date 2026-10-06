SELECT
    MachineID,
    MachineCode,
    MachineName,
    LineID,
    Section
FROM dbo.tbl_Machine
WHERE IsActive = 1
ORDER BY MachineName;