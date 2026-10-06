UPDATE work_orders
SET 
    XFRMR_Serial = :XFRMR_Serial,
    last_sync_erp = GETDATE()
WHERE serial_number = :serial_number;