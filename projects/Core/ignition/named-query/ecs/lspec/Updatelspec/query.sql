IF EXISTS (SELECT 1 FROM lspec_metadata WHERE lspec_id = :lspec_id and KVA is null)
BEGIN
    UPDATE lspec_metadata
    SET 
        revision = revision + 1,   -- optional (if you want versioning)
        KVA = :KVA,
        hv1_bil = :hv1_bil,
        PRODCOMP = :PRODCOMP,
        last_sync = GETDATE()
    WHERE lspec_id = :lspec_id
END