IF NOT EXISTS (SELECT 1 FROM lspec_metadata WHERE lspec_id = :lspec_id)
BEGIN
    INSERT INTO lspec_metadata (
        lspec_id, 
        revision, 
        lv_winding_time, 
        hv_winding_time, 
        total_coil_time, 
        total_winding_time, 
        erp_source, 
        is_active,
        KVA,
        hv1_bil,
        PRODCOMP,
        last_sync
    )
    VALUES (
        :lspec_id, 
        1, 
        :lv_winding, 
        :hv_winding, 
        :total_coil, 
        :total_winding, 
        :source_val, 
        1,
        :KVA,
        :hv1_bil,
        :PRODCOMP,
        GETDATE() -- Captures the current date/time
    )
END