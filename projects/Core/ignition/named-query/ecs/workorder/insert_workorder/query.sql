IF NOT EXISTS (SELECT 1 FROM work_orders WHERE serial_number = :serial_number)
BEGIN
    INSERT INTO work_orders (
        po_number, 
        serial_number, 
        lspec_id, 
        scheduled_start, 
        op_status, 
        serial_status,
        XFRMR_Serial,
        last_sync_erp
    )
    VALUES (
        :po_number, 
        :serial_number, 
        :lspec_id, 
        :scheduled_start, 
        :op_status, 
        :serial_status,
        :XFRMR_Serial,
        GETDATE()
    )
END