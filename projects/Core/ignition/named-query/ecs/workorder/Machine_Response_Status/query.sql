SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1
            FROM ABBMachineResponseStatus
            WHERE Serial_Num = :Serial_Num
              AND (
                    (:action = 4 AND MR_start = 1)
                 OR (:action = 16 AND MR_Done = 1)
              )
        )
        THEN 1 
        ELSE 0 
    END AS MR_Status_Flag