-- schema is named ex_zpl_label_printing. (instead of public)
select printer_name, ip_address, offset_x_mm, offset_y_mm
from ex_zpl_label_printing.ex_zlp_label_printer_settings
order by printer_name