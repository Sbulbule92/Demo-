WITH ClampedDowntime AS (
    SELECT 
         LogID
        ,IIF(StartTime > :StartTime, StartTime, :StartTime) AS EffectiveStart
        -- For R8/R9: deduct 30 min from the clamped end
        ,CASE 
            WHEN ReasonID IN (8, 9)
                THEN DATEADD(MINUTE, -30, IIF(EndTime < :EndTime, EndTime, :EndTime))
            ELSE 
                IIF(EndTime < :EndTime, EndTime, :EndTime)
         END AS EffectiveEnd
    FROM tbl_DowntimeLog
    WHERE 
        DurationMinutes > 0
        AND DurationMinutes IS NOT NULL
        AND (:MachineID IS NULL OR MachineID = :MachineID)
        AND StartTime < :EndTime
        AND EndTime > :StartTime
        -- Include R8/R9 only when DurationMinutes > 30
--        AND (ReasonID NOT IN (8, 9) OR DurationMinutes > 30)
),
ValidDowntime AS (
    -- Guard: drop rows where 30-min deduction caused EffectiveEnd <= EffectiveStart
    -- (can happen when a R8/R9 event is mostly outside the shift window)
    SELECT LogID, EffectiveStart, EffectiveEnd
    FROM ClampedDowntime
    WHERE EffectiveEnd > EffectiveStart
),
RankedDowntime AS (
    SELECT 
        *,
        MAX(EffectiveEnd) OVER (
            ORDER BY EffectiveStart 
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS PreviousMaxEnd
    FROM ValidDowntime          -- <-- changed from ClampedDowntime
),
IslandStarts AS (
    SELECT 
        *,
        CASE 
            WHEN PreviousMaxEnd IS NULL OR EffectiveStart > PreviousMaxEnd 
            THEN 1 
            ELSE 0 
        END AS IsNewIsland
    FROM RankedDowntime
),
IslandGroups AS (
    SELECT 
        *,
        SUM(IsNewIsland) OVER (ORDER BY EffectiveStart) AS IslandID
    FROM IslandStarts
),
MergedDowntime AS (
    SELECT 
         IslandID
        ,MIN(EffectiveStart) AS PeriodStart
        ,MAX(EffectiveEnd) AS PeriodEnd
        ,DATEDIFF(MINUTE, MIN(EffectiveStart), MAX(EffectiveEnd)) AS PeriodMinutes
    FROM IslandGroups
    GROUP BY IslandID
)
SELECT IIF(SUM(PeriodMinutes) < 1170, SUM(PeriodMinutes), 1170)
FROM MergedDowntime