UPDATE work_orders 
SET 
op_status = :op_status
WHERE serial_number = :serial_number 
    AND po_number = :po_number;