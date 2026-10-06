IF :serial IS NULL
    RETURN; 


MERGE INTO XFR_Status AS target
USING (
    SELECT 
        :serial AS XFR_Serial_Number,
        :tank AS Tank_Status,
        :core AS Core_Status
) AS source
ON target.XFR_Serial_Number = source.XFR_Serial_Number

WHEN MATCHED THEN
    UPDATE SET
        target.Tank_Status = source.Tank_Status,
        target.Core_Status = source.Core_Status,
        target.LastUpdate = GETDATE()

WHEN NOT MATCHED THEN
    INSERT (
        XFR_Serial_Number,
        Tank_Status,
        Core_Status,
        LastUpdate
    )
    VALUES (
        source.XFR_Serial_Number,
        source.Tank_Status,
        source.Core_Status,
        GETDATE()
    );