SELECT ManufacturerName
FROM tbl_WireManufacturer
WHERE IsActive = 1
ORDER BY SortOrder, ManufacturerName;