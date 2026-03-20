UPDATE dbo.TankPrograms
SET work_status = 2
WHERE serial_number = :serial_number and program_name = :program_name;

