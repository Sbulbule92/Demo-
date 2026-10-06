UPDATE work_orders 
SET 
    op_status = :op_status,
    machine_id = :machine_id,

    actual_start = CASE 
        WHEN :op_status = 4 AND actual_start IS NULL THEN GETDATE() 
        ELSE actual_start 
    END,

    actual_end = CASE 
        WHEN :op_status = 16 THEN GETDATE() 
        ELSE actual_end 
    END,

    StartUser = CASE 
        WHEN :op_status = 4 AND StartUser IS NULL THEN :user_name 
        ELSE StartUser 
    END,

    EndUser = CASE 
        WHEN :op_status = 16 AND EndUser IS NULL THEN :user_name 
        ELSE EndUser 
    END,

    last_machine_update = GETDATE()

WHERE 
    serial_number = :serial_number 
    AND po_number = :po_number;