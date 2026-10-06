
SELECT 
    W.po_number,
    W.serial_number,
    W.machine_id,

    L.PRODCOMP + '_' + CAST(L.KVA AS VARCHAR) + '_' + CAST(L.hv1_bil AS VARCHAR) AS program_name,

    W.is_priority AS priority,

    ISNULL(X.Tank_Status, 'Ready') AS tank_status,   -- 🔴 CHANGE: added join field
    ISNULL(X.Core_Status, 'Ready') AS core_status,   -- 🔴 CHANGE: added join field

    W.op_status,
     ECS.Op_Status AS ecs_op_status

FROM work_orders W

INNER JOIN lspec_metadata L 
    ON W.lspec_id = L.lspec_id

LEFT JOIN XFR_Status X     -- 🔴 CHANGE: new table join added
    ON W.serial_number = X.XFR_Serial_Number   -- 🔴 CHANGE: mapping key
LEFT JOIN [Ignition].[dbo].[ECS_OPstatus] ECS
    ON W.serial_number = ECS.SerialNumber

WHERE W.op_status <> 16 
      AND (ECS.Op_Status IS NULL OR ECS.Op_Status <> 16)
ORDER BY W.is_priority DESC; 