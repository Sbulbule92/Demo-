SELECT 
    m.MachineCode,
    m.MachineID,
    m.MachineName,
    l.LineName,
    m.EquipmentName,
    m.OPRID,
    m.LineID,
    m.Section,
    m.SupplierName,
    m.Section + '/UDT_' + m.MachineCode + '_OEE' AS basePath
FROM [dbo].[tbl_Machine] m
INNER JOIN [dbo].[tbl_Line] l 
    ON m.LineID = l.LineID
WHERE m.IsActive = 1;