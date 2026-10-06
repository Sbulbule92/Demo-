INSERT INTO tbl_Machine (MachineCode, MachineName, LineID, Section, IPAddress,
    SupplierName, EquipmentName, OPRID, Description, IsActive)
VALUES (:MachineCode, :MachineName, :LineID, :Section, :IPAddress,
    :SupplierName, :EquipmentName, :OPRID, :Description, :IsActive);