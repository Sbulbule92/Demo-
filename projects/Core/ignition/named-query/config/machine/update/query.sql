UPDATE tbl_Machine SET MachineCode=:MachineCode, MachineName=:MachineName,
    LineID=:LineID, Section=:Section, IPAddress=:IPAddress,
    SupplierName=:SupplierName, EquipmentName=:EquipmentName, OPRID=:OPRID,
    Description=:Description, IsActive=:IsActive WHERE MachineID=:MachineID;