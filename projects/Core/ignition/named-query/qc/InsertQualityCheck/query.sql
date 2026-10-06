IF EXISTS (SELECT 1 FROM quality_checks WHERE job_id = :jobId)
    UPDATE quality_checks
    SET line_id          = :lineId,
        machine_id       = :machineId,
        shift_id         = :shiftId,
        core_shifted     = :coreShifted,
        ins_thickness_ok = :insThickness,
        ins_width_ok     = :insWidth,
        long_wound_in    = :longWound,
        short_wound_in   = :shortWound,
        comments         = :comments,
        created_by       = :username
    WHERE job_id = :jobId
ELSE
    INSERT INTO quality_checks
        (job_id, line_id, machine_id, shift_id, core_shifted,
         ins_thickness_ok, ins_width_ok, long_wound_in, short_wound_in,
         comments, created_by)
    VALUES
        (:jobId, :lineId, :machineId, :shiftId, :coreShifted,
         :insThickness, :insWidth, :longWound, :shortWound,
         :comments, :username);