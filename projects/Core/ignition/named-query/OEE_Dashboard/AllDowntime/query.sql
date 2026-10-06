WITH ClampedDowntime AS (
    SELECT 
         d.LogID
        ,d.MachineID
        ,d.ReasonID
        ,r.ReasonName
        ,d.Remarks
        ,d.UserName
        ,(CASE WHEN d.ReasonID in (1, 2, 8, 9) Then 'Planned' ELSE 'Unplanned' END) AS DTtype
        ,IIF(d.StartTime > :StartTime, d.StartTime, :StartTime)                     AS ClampedStart
        ,IIF(d.EndTime > :EndTime or d.EndTime is null, :EndTime, d.EndTime)        AS ClampedEnd
    FROM tbl_DowntimeLog AS d
    JOIN tbl_DowntimeReason AS r ON r.ReasonID = d.ReasonID
    WHERE 
        d.MachineID = :MachineID
        AND d.StartTime < :EndTime
        AND (d.EndTime  > :StartTime)
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
        ,ReasonID
        ,DTtype
        ,UserName
        ,Remarks
        ,MIN(ClampedStart)                                              AS PeriodStart
        ,MAX(ClampedEnd)                                                AS PeriodEnd
        ,DATEDIFF(MINUTE, MIN(ClampedStart), MAX(ClampedEnd))          AS PeriodMinutes
        ,STRING_AGG(CAST(LogID AS VARCHAR), ',')                        AS MergedLogIDs
        ,STRING_AGG(ReasonName, '; ')                                   AS MergedReasons
    FROM GroupedDowntime
    GROUP BY DowntimeGroup, UserName, Remarks, MachineID, ReasonID, DTtype
),
-- ↓ Pick only the ReasonID 9 row with the highest duration per machine
DeduplicatedDowntime AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY 
                MachineID,
                ReasonID
            ORDER BY PeriodMinutes DESC  -- ← longest duration wins
        ) AS rn
    FROM MergedDowntime
)
SELECT 
     MergedLogIDs                                                       AS LogIDs
    ,MachineID                                                          AS MachineID
    ,ReasonID
    ,PeriodStart                                                        AS StartTime
    ,PeriodEnd                                                          AS EndTime
    ,DTtype
    ,Remarks
    ,UserName
    ,MergedReasons                                                      AS ReasonName
    ,IIF(PeriodMinutes < 1170, PeriodMinutes, 1170)                    AS ShiftDurationMinutes
    ,IIF(PeriodMinutes < 1170, PeriodMinutes, 1170)                    AS TotalDurationMinutes
FROM DeduplicatedDowntime
WHERE ReasonID <> 9 OR rn = 1   -- ← all other reasons pass through, only best ReasonID 9 kept
ORDER BY PeriodStart