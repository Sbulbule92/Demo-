UPDATE work_orders 
SET 
    op_status = :op_status,
    machine_id = :machine_id,
    actual_start = CASE 
        WHEN :op_status = 4 THEN GETDATE() 
        ELSE actual_start 
    END,
    actual_end = CASE 
        WHEN :op_status = 16 THEN GETDATE() 
        ELSE actual_end 
    END,
    
    last_machine_update = GETDATE()
WHERE 
    serial_number = :serial_number 
    AND po_number = :po_number;