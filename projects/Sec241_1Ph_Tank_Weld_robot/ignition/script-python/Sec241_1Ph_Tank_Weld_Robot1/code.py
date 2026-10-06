query = """
SELECT DISTINCT
    t.[TANK],
    l.[Height],
    l.[Width],
    l.[Depth],
    CASE
        WHEN d.[TANK_MATERIAL] IN ('CARBON_STEEL', '1', 'M', 'MILD') THEN 'MILD'
        WHEN d.[TANK_MATERIAL] IS NULL OR d.[TANK_MATERIAL] = '' THEN 'Error'
        ELSE 'SST'
    END AS [MAT_TYPE],
    t.[BASE_HT]
FROM [MachineReady].[dbo].[vw_ABB_TankWeldDimensionLookup] AS l
JOIN [MachineReady].[Engineering].[Transformer_Chars] AS t
  ON t.[TANK] = l.[TANK]
JOIN [MachineReady].[dbo].[TANK_DATA] AS d
  ON d.[Design_no] = t.[Design]
WHERE t.[TANK] = ?
"""
ds = system.db.runPrepQuery(query, ['J431DRFQ'], 'ECSMachineReadyTestServer')

# Print header
headers = list(ds.getColumnNames())
print(','.join(headers))

# Print each row
for r in range(ds.getRowCount()):
    vals = []
    for c in range(ds.getColumnCount()):
        v = ds.getValueAt(r, c)
        vals.append('' if v is None else unicode(v))
    print(','.join(vals))