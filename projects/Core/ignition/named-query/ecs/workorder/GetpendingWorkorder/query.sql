SELECT 
    W.po_number,
    W.serial_number,
 
    L.PRODCOMP + '_' + CAST(L.KVA AS VARCHAR) + '_' + CAST(L.hv1_bil AS VARCHAR) AS program_name,
 
    W.is_priority AS priority,
 
    ISNULL(X.Tank_Status, 'Ready') AS tank_status,
    ISNULL(X.Core_Status, 'Ready') AS core_status,
 
    W.op_status AS op_status,
    ECS.Op_Status AS ecs_op_status,
 
    WIPDATA.actual_num_turns
 
FROM work_orders W
 
INNER JOIN lspec_metadata L 
    ON W.lspec_id = L.lspec_id
 
LEFT JOIN XFR_Status X     
    ON W.serial_number = X.XFR_Serial_Number  
 
LEFT JOIN [Ignition].[dbo].[ECS_OPstatus] ECS
    ON W.serial_number = ECS.SerialNumber
 
LEFT JOIN (
    SELECT serial_number, actual_num_turns
    FROM (
        SELECT 
            serial_number,
            actual_num_turns,
            ROW_NUMBER() OVER (
                PARTITION BY 
                    LEFT(serial_number, CHARINDEX('_CoilWind_', serial_number + '_CoilWind_') - 1)
                ORDER BY update_time DESC
            ) AS rn
        FROM wo_event_history
        WHERE event_type_id IN (8, 32)
    ) t
    WHERE rn = 1
) WIPDATA
    ON W.serial_number = 
       LEFT(WIPDATA.serial_number, CHARINDEX('_CoilWind_', WIPDATA.serial_number + '_CoilWind_') - 1)
 
-- ✅ FINAL FIXED LOGIC
WHERE 
    W.Op_Status <> 16
    AND (ECS.Op_Status IS NULL OR ECS.Op_Status <> 16)
 
ORDER BY CASE 
        WHEN W.op_status IN (8, 32) THEN 1
        ELSE 0 
    END,
    W.is_priority DESC;