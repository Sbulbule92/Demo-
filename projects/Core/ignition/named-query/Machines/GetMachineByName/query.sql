SELECT 
    MachineID,
    MachineCode,
    MachineName,EquipmentName,OPRID,
    LineID,Section,Section + '/UDT_' + MachineCode + '_OEE' AS basePath
FROM [dbo].[tbl_Machine]
WHERE IPAddress = :ipaddress