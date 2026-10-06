UPDATE work_orders
SET is_priority=  :priority 
OUTPUT inserted.serial_number
WHERE serial_number = :serial_number 