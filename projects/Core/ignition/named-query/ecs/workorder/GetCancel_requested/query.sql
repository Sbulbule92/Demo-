SELECT w.po_number,
    W.serial_number,
    L.PRODCOMP + '_' + CAST(L.KVA AS VARCHAR) + '_' + CAST(L.hv1_bil AS VARCHAR) AS program_name,
    w.machine_id,
    W.is_priority AS priority,
    '' AS core_status,
    '' AS tank_status,
    W.op_status
FROM work_orders W
INNER JOIN lspec_metadata L ON W.lspec_id = L.lspec_id
WHERE W.op_status =45
ORDER BY W.is_priority DESC