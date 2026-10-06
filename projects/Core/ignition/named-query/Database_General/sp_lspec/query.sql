DOnt Fire the code




--CREATE OR ALTER PROCEDURE dbo.sp_Process_lspec_staging
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        DECLARE @Inserted INT = 0;
        DECLARE @Updated INT = 0;
        DECLARE @Matched INT = 0;
        DECLARE @NoChange INT = 0;

        DECLARE @MergeOutput TABLE (action NVARCHAR(10));

        -- Count matched rows BEFORE merge
        SELECT @Matched = COUNT(*)
        FROM stg_lspec s
        INNER JOIN lspec_metadata t
            ON t.lspec_id = s.LSPEC;

        MERGE INTO lspec_metadata AS target
        USING stg_lspec AS src
        ON target.lspec_id = src.LSPEC

        WHEN MATCHED AND (
            ISNULL(target.lv_winding_time,0) <> ISNULL(src.LV_Winding,0)
            OR ISNULL(target.hv_winding_time,0) <> ISNULL(src.HV_Winding,0)
            OR ISNULL(target.total_coil_time,0) <> ISNULL(src.Total_Coil_Time,0)
            OR ISNULL(target.total_winding_time,0) <> ISNULL(src.Total_Winding_Time,0)
            OR ISNULL(target.kva,0) <> ISNULL(src.KVA,0)
            OR ISNULL(target.hv1_bil,0) <> ISNULL(src.hv1_bil,0)
            OR ISNULL(target.PRODCOMP,'') <> ISNULL(src.PRODCOMP,'')
        )
        THEN UPDATE SET
            target.revision = target.revision + 1,
            target.lv_winding_time = src.LV_Winding,
            target.hv_winding_time = src.HV_Winding,
            target.total_coil_time = src.Total_Coil_Time,
            target.total_winding_time = src.Total_Winding_Time,
            target.erp_source = src.Source,
            target.is_active = 1,
            target.last_sync = GETDATE(),
            target.kva = src.KVA,
            target.hv1_bil = src.hv1_bil,
            target.PRODCOMP = src.PRODCOMP

        WHEN NOT MATCHED THEN
            INSERT (
                lspec_id, revision, lv_winding_time, hv_winding_time,
                total_coil_time, total_winding_time, erp_source,
                is_active, last_sync, kva, hv1_bil, PRODCOMP
            )
            VALUES (
                src.LSPEC, 1, src.LV_Winding, src.HV_Winding,
                src.Total_Coil_Time, src.Total_Winding_Time,
                src.Source, 1, GETDATE(),
                src.KVA, src.hv1_bil, src.PRODCOMP
            )

        OUTPUT $action INTO @MergeOutput;

        -- Counts
        SELECT @Inserted = COUNT(*) FROM @MergeOutput WHERE action = 'INSERT';
        SELECT @Updated = COUNT(*) FROM @MergeOutput WHERE action = 'UPDATE';

        -- No Change Calculation
        SET @NoChange = @Matched - @Updated;

        -- ✅ FINAL RESPONSE
        SELECT 
            1 AS Status,
            @Inserted AS InsertedCount,
            @Updated AS UpdatedCount,
            @NoChange AS NoChangeCount,
            (@Inserted + @Updated + @NoChange) AS TotalProcessed,
            NULL AS ErrorMessage;

    END TRY
    BEGIN CATCH

        SELECT 
            0 AS Status,
            0 AS InsertedCount,
            0 AS UpdatedCount,
            0 AS NoChangeCount,
            0 AS TotalProcessed,
            ERROR_MESSAGE() AS ErrorMessage,
            ERROR_LINE() AS ErrorLine,
            ERROR_PROCEDURE() AS ErrorProcedure;

    END CATCH
END;