SELECT TOP (1)
       [LegacySerial],
       [JCSerial]
FROM [Engineering].[dbo].[vw_seriallinkage]
WHERE CHARINDEX('J', [LegacySerial]) > 1
  AND SUBSTRING(
          [LegacySerial],
          CHARINDEX('J', [LegacySerial]) + 1,
          LEN([LegacySerial])
      ) = LTRIM(RTRIM(:baseLegacySerial))
  AND TRY_CONVERT(
          int,
          LEFT(
              [LegacySerial],
              CHARINDEX('J', [LegacySerial]) - 1
          )
      ) IS NOT NULL
ORDER BY
    TRY_CONVERT(
        int,
        LEFT(
            [LegacySerial],
            CHARINDEX('J', [LegacySerial]) - 1
        )
    ) DESC;