UPDATE dbo.TankPrograms
SET work_status = 1
WHERE serial_number = :serial_number and program_name = :program_name;

