-- schema is named ex_zpl_label_printing. (instead of public)
select u.user_name 
from ex_zpl_label_printing.ex_zlp_label_users as u
left join ex_zpl_label_printing.ex_zlp_label_templates as t on t.id = u.ex_zlp_label_templates_id
where t.label_name = :labelName 
order by u.user_name