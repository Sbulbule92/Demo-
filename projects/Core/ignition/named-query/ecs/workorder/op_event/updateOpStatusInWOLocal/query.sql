UPDATE work_orders
SET op_status = :status
WHERE serial_number = :serial_number