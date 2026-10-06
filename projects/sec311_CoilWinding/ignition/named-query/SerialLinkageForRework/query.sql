SELECT
    JCSerial,
    LegacySerial
FROM [Engineering].[dbo].[vw_seriallinkage]
WHERE JCSerial = :JCserial