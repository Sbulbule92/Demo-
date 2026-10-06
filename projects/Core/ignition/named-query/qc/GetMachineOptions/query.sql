SELECT MachineID, MachineCode
FROM tbl_Machine
WHERE IsActive = 1
  AND (:lineId = -1 OR LineID = :lineId)
ORDER BY MachineCode;