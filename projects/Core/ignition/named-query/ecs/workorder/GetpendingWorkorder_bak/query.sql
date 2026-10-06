SELECT 
    W.po_number,
    W.serial_number,

    L.PRODCOMP + '_' + CAST(L.KVA AS VARCHAR) + '_' + CAST(L.hv1_bil AS VARCHAR) AS program_name,

    W.is_priority AS priority,

    ISNULL(X.Tank_Status, 'Ready') AS tank_status,
    ISNULL(X.Core_Status, 'Ready') AS core_status,

    W.op_status,

    WIPDATA.actual_num_turns   -- ✅ changed from wip

FROM work_orders W

INNER JOIN lspec_metadata L 
    ON W.lspec_id = L.lspec_id

LEFT JOIN XFR_Status X     
    ON W.serial_number = X.XFR_Serial_Number  

-- ✅ ACTUAL TURNS LOGIC (latest 8 or 32)
LEFT JOIN (
    SELECT serial_number, actual_num_turns
    FROM (
        SELECT 
            serial_number,
            actual_num_turns,
            ROW_NUMBER() OVER (
                PARTITION BY serial_number 
                ORDER BY update_time DESC
            ) AS rn
        FROM wo_event_history
        WHERE event_type_id IN (8, 32)
    ) t
    WHERE rn = 1
) WIPDATA

-- ⚠️ Choose ONE based on your data

-- 👉 If exact match:
ON W.serial_number = WIPDATA.serial_number

-- 👉 If suffix exists (_CoilWind_1 etc), use this:
-- ON W.serial_number = LEFT(WIPDATA.serial_number, CHARINDEX('_', WIPDATA.serial_number) - 1)

WHERE W.op_status <> 16 

ORDER BY W.is_priority DESC;