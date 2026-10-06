
# In Project Library script named W1Priority
def run():
    """
    Summarizes W1 named query by Material and ScheduledStart,
    then writes the result to memory tag [default]W1P.
    """
    from system.dataset import toDataSet

    # 1. Call the named query W1
    params = {"clear_conn": "ECSMachineReady"}
    result = system.db.runNamedQuery("W1", params)

    # 2. Summarize data by Material and ScheduledStart
    summary_dict = {}
    for row in range(result.getRowCount()):
        material = result.getValueAt(row, "Material")
        quantity = result.getValueAt(row, "Quantity")
        scheduled_start = result.getValueAt(row, "ScheduledStart")

        key = (material, scheduled_start)
        summary_dict[key] = summary_dict.get(key, 0) + quantity

    # 3. Build summarized dataset
    columns = ["Material", "Quantity", "ScheduledStart"]
    data_out = [[mat, qty, sched] for (mat, sched), qty in summary_dict.items()]
    new_dataset = toDataSet(columns, data_out)

    # 4. Write dataset to memory tag [default]W1P
    system.tag.writeBlocking(["[default]Sec211/Hervoss/DataAutomation/W1P"], [new_dataset])