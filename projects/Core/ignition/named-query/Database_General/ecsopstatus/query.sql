----CREATE OR ALTER PROCEDURE dbo.sp_Insert_stg_ecs_op_status_JSON
    @json NVARCHAR(MAX)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @RowsInserted INT = 0;

    BEGIN TRY

        INSERT INTO stg_ecs_op_status
        (
            SerialNumber,
            OP_Status,
            Scheduled_Start,
            ECS_AWAIT
        )
        SELECT 
            SerialNumber,
            OP_Status,
            Scheduled_Start,
            ECS_AWAIT
        FROM OPENJSON(@json)
        WITH (
            SerialNumber VARCHAR(100),
            OP_Status INT,
            Scheduled_Start DATETIME,
            ECS_AWAIT BIT
        );

        SET @RowsInserted = @@ROWCOUNT;

        -- ✅ Return success response
        SELECT 
            'SUCCESS' AS Status,
            'Data inserted into staging successfully' AS Message,
            @RowsInserted AS RowsInserted;

    END TRY
    BEGIN CATCH

        -- ❌ Return error response
        SELECT 
            'FAILED' AS Status,
            ERROR_MESSAGE() AS Message,
            0 AS RowsInserted;

    END CATCH
END;