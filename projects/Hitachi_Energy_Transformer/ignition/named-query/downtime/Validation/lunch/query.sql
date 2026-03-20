SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1
            FROM dbo.tbl_DowntimeLog
            WHERE ReasonID = 30
              AND StartTime >= :startTime
              AND StartTime <  :endTime
        )
        THEN 1 ELSE 0
    END AS LunchExists;
