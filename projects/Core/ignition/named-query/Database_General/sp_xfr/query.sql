CREATE OR ALTER PROCEDURE dbo.sp_Process_xfr_status_staging
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY

        DECLARE 
            @Inserted INT = 0,
            @Updated INT = 0,
            @NoChange INT = 0;

        DECLARE @MergeOutput TABLE (action NVARCHAR(10));

        MERGE INTO xfr_status AS target
        USING stg_xfr_status AS src
        ON target.XFR_Serial_Number = src.XFR_Serial_Number

        -- 🔹 UPDATE only if data changed
        WHEN MATCHED AND (
            ISNULL(target.Tank_Status,'') <> ISNULL(src.Tank_Status,'')
            OR ISNULL(target.Core_Status,'') <> ISNULL(src.Core_Status,'')
        )
        THEN UPDATE SET
            target.Tank_Status = src.Tank_Status,
            target.Core_Status = src.Core_Status,
            target.Last_Updated = GETDATE()

        -- 🔹 INSERT new records
        WHEN NOT MATCHED THEN
            INSERT (
                XFR_Serial_Number,
                Tank_Status,
                Core_Status,
                Last_Updated
            )
            VALUES (
                src.XFR_Serial_Number,
                src.Tank_Status,
                src.Core_Status,
                GETDATE()
            )

        OUTPUT $action INTO @MergeOutput;

        -- 🔹 Count results
        SELECT 
            @Inserted = SUM(CASE WHEN action = 'INSERT' THEN 1 ELSE 0 END),
            @Updated  = SUM(CASE WHEN action = 'UPDATE' THEN 1 ELSE 0 END)
        FROM @MergeOutput;

        -- 🔹 No Change = total staging - (insert + update)
        SELECT @NoChange = COUNT(*) FROM stg_xfr_status;

        SET @NoChange = @NoChange - (@Inserted + @Updated);

        -- ✅ SUCCESS RESPONSE
        SELECT 
            1 AS Status,
            @Inserted AS InsertCount,
            @Updated AS UpdateCount,
            @NoChange AS NoChangeCount,
            NULL AS ErrorMessage;

    END TRY
    BEGIN CATCH

        -- ❌ FAILURE RESPONSE
        SELECT 
            0 AS Status,
            0 AS InsertCount,
            0 AS UpdateCount,
            0 AS NoChangeCount,
            ERROR_MESSAGE() AS ErrorMessage;

    END CATCH
END;