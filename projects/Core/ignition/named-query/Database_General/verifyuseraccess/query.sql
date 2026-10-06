SELECT 
    dp.name AS UserName,
    o.name AS ObjectName,
    p.permission_name,
    p.state_desc
FROM sys.database_permissions p
JOIN sys.objects o 
    ON p.major_id = o.object_id
JOIN sys.database_principals dp 
    ON p.grantee_principal_id = dp.principal_id
WHERE dp.name = :userName
AND o.name = :tableName