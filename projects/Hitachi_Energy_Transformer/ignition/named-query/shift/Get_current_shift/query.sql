SELECT TOP 1
    ShiftID,
    ShiftCode,
    ShiftName,

    -- Shift Start DateTime
    CASE
        -- Normal shift (same day)
        WHEN StartTime < EndTime THEN
            CAST(CAST(GETDATE() AS date) AS datetime)
            + CAST(StartTime AS datetime)

        -- Overnight shift
        WHEN StartTime > EndTime
             AND CAST(GETDATE() AS time) >= StartTime THEN
            CAST(CAST(GETDATE() AS date) AS datetime)
            + CAST(StartTime AS datetime)

        -- Overnight shift (after midnight)
        ELSE
            CAST(DATEADD(day, -1, CAST(GETDATE() AS date)) AS datetime)
            + CAST(StartTime AS datetime)
    END AS ShiftStartDateTime,

    -- Shift End DateTime
    CASE
        -- Normal shift (same day)
        WHEN StartTime < EndTime THEN
            CAST(CAST(GETDATE() AS date) AS datetime)
            + CAST(EndTime AS datetime)

        -- Overnight shift
        WHEN StartTime > EndTime
             AND CAST(GETDATE() AS time) >= StartTime THEN
            CAST(DATEADD(day, 1, CAST(GETDATE() AS date)) AS datetime)
            + CAST(EndTime AS datetime)

        -- Overnight shift (after midnight)
        ELSE
            CAST(CAST(GETDATE() AS date) AS datetime)
            + CAST(EndTime AS datetime)
    END AS ShiftEndDateTime

FROM dbo.tbl_Shift
WHERE IsActive = 1
AND (
        (StartTime < EndTime
         AND CAST(GETDATE() AS time) >= StartTime
         AND CAST(GETDATE() AS time) < EndTime)

        OR

        (StartTime > EndTime
         AND (
              CAST(GETDATE() AS time) >= StartTime
              OR CAST(GETDATE() AS time) < EndTime
         ))
    )
ORDER BY ShiftID;
