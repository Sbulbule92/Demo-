WITH ClampedDowntime AS (
    SELECT 
         d.LogID
        ,d.MachineID
        ,d.ReasonID
        ,r.ReasonName
        ,d.Remarks
        ,d.UserName
        ,CAST(CASE WHEN d.EndTime IS NULL THEN 1 ELSE 0 END AS BIT) AS IsOngoing  -- ← track null
        ,IIF(d.StartTime > :StartTime, d.StartTime, :StartTime)                    AS ClampedStart
        ,IIF(d.EndTime IS NULL OR d.EndTime > :EndTime, :EndTime, d.EndTime)       AS ClampedEnd
    FROM tbl_DowntimeLog AS d
    JOIN tbl_DowntimeReason AS r ON r.ReasonID = d.ReasonID
    WHERE 
        d.MachineID = :MachineID
        AND d.StartTime < :EndTime
        AND (d.EndTime > :StartTime)
        
),
OrderedDowntime AS (
    SELECT 
         *
        ,LAG(ClampedEnd) OVER (ORDER BY ClampedStart, ClampedEnd) AS PrevEnd
    FROM ClampedDowntime
),
GroupedDowntime AS (
    SELECT 
         *
        ,SUM(CASE 
            WHEN PrevEnd IS NULL OR ClampedStart > PrevEnd THEN 1 
            ELSE 0 
        END) OVER (ORDER BY ClampedStart, ClampedEnd) AS DowntimeGroup
    FROM OrderedDowntime
),
MergedDowntime AS (
    SELECT 
         DowntimeGroup
         ,MachineID
        , ReasonID
        ,UserName
        ,Remarks
        ,MIN(ClampedStart)                                              AS PeriodStart
        ,MAX(ClampedEnd)                                                AS PeriodEnd
        ,DATEDIFF(MINUTE, MIN(ClampedStart), MAX(ClampedEnd))          AS PeriodMinutes
        ,MAX(CAST(IsOngoing AS TINYINT))                                AS HasOngoing   -- ← 1 if any merged row is ongoing
        ,STRING_AGG(CAST(LogID AS VARCHAR), ',')                        AS MergedLogIDs
        ,STRING_AGG(ReasonName, '; ')                                   AS MergedReasons
    FROM GroupedDowntime
    GROUP BY DowntimeGroup, UserName, Remarks, MachineID, ReasonID
)
SELECT  
        IIF(SUM(PeriodMinutes) > 0, SUM(PeriodMinutes), 0) AS duration,
        COUNT(MergedLogIDs)                                               AS reason_count,
        MergedReasons                                                    AS ReasonName
--     MergedLogIDs                                                               AS LogIDs
--    ,MachineID                                                                 AS MachineID
--    , ReasonID
--    ,PeriodStart                                                                AS StartTime
--    ,IIF(HasOngoing = 1, NULL, PeriodEnd)                                       AS EndTime              -- ← blank if ongoing
--    ,Remarks
--    ,UserName
--    ,MergedReasons                                                              AS ReasonName
--    ,IIF(HasOngoing = 1, NULL, IIF(PeriodMinutes < 1170, PeriodMinutes, 1170)) AS ShiftDurationMinutes  -- ← null if ongoing
--    ,IIF(HasOngoing = 1, NULL, IIF(PeriodMinutes < 1170, PeriodMinutes, 1170)) AS TotalDurationMinutes  -- ← null if ongoing
FROM MergedDowntime
GROUP BY MergedReasons