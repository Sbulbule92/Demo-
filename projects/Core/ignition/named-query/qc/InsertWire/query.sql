INSERT INTO hv_wires
    (job_id, wire_seq, wire_manufacturer, lot_number, coating_type,
     round_wire_diameter, width_inches, thickness_inches, hv_wire_tension)
VALUES
    (:jobId, :wireSeq, :mfr, :lot, :coating,
     :dia, :width, :thick, :tension);