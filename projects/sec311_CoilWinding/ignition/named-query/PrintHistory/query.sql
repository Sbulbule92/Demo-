SELECT TOP 500
    UserName,
    Serial,
    PrintDate
FROM CW_Supervisor_Label_Print
WHERE
    (
        :Serial IS NULL
        OR :Serial = ''
        OR Serial LIKE '%' + :Serial + '%'
    )
AND
    (
        :UserName IS NULL
        OR :UserName = ''
        OR UserName LIKE '%' + :UserName + '%'
    )
ORDER BY PrintDate DESC