UPDATE tbl_Shift SET ShiftCode=:ShiftCode, ShiftName=:ShiftName,
    StartTime=:StartTime, EndTime=:EndTime, Description=:Description,
    IsActive=:IsActive WHERE ShiftID=:ShiftID;