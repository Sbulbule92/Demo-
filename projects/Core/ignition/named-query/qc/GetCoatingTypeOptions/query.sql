SELECT CoatingTypeName
FROM tbl_CoatingType
WHERE IsActive = 1
ORDER BY SortOrder, CoatingTypeName;