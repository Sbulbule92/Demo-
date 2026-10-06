DECLARE @UserName  NVARCHAR(100) =  :UserName 
DECLARE @StartDate DATETIME      =  :StartTime 
DECLARE @EndDate   DATETIME      =  :EndTime 

-- ↓ Rank ReasonID 9 rows by DurationMinutes, longest = rn 1
;WITH DeduplicatedDowntime AS (
    SELECT
        dl.LogID,
        dl.ReasonID,
        dl.StartTime,
        dl.EndTime,
        dr.ReasonName,
        dl.Remarks,
        dl.DurationMinutes,
        ROW_NUMBER() OVER (
            PARTITION BY 
                dl.UserName,
                dl.ReasonID
            ORDER BY dl.DurationMinutes DESC  -- ← longest duration wins
        ) AS rn
    FROM tbl_DowntimeLog dl
    INNER JOIN tbl_DowntimeReason dr ON dr.ReasonID = dl.ReasonID
    WHERE
        dl.UserName  = @UserName
        AND dl.StartTime >= @StartDate
        AND dl.StartTime <= @EndDate
)
SELECT
     LogID
    ,StartTime
    ,EndTime
    ,ReasonName
    ,Remarks
    ,DurationMinutes
FROM DeduplicatedDowntime
WHERE ReasonID <> 9 OR rn = 1   -- ← all other reasons pass through, only best ReasonID 9 kept
ORDER BY StartTime ASC