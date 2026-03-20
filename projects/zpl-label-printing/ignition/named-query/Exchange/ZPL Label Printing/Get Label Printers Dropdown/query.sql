-- schema is named ex_zpl_label_printing. (instead of public)
select printer_name as label, ip_address as value
from ex_zpl_label_printing.ex_zlp_label_printer_settings
order by printer_name