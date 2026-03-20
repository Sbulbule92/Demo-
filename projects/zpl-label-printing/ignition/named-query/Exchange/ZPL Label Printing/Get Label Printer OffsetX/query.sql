-- schema is named ex_zpl_label_printing. (instead of public)
select offset_x_mm
from ex_zpl_label_printing.ex_zlp_label_printer_settings
where ip_address = :ipAddress