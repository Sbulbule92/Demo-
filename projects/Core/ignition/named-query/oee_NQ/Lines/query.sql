SELECT
    LineID,
    LineCode,
    LineName
FROM dbo.tbl_Line
WHERE IsActive = 1
ORDER BY LineName;