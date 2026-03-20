def calculate_salary(structure, basic,
                     days_in_month, days_present):
    if days_in_month == 0:
        days_in_month = 30

    per_day      = basic / days_in_month
    earned_basic = round(per_day * days_present, 2)

    def calc(ctype, cvalue):
        if ctype == 'percent':
            return round(earned_basic * cvalue / 100, 2)
        else:
            return round(
                (cvalue / days_in_month) * days_present,
                2
            )

    da      = calc(structure.da_type,
                   structure.da_value)
    hra     = calc(structure.hra_type,
                   structure.hra_value)
    special = calc(structure.special_type,
                   structure.special_value)
    bonus   = calc(structure.bonus_type,
                   structure.bonus_value)

    # Custom components
    custom_total = 0
    custom_items = []
    if hasattr(structure, 'custom_components'):
        for comp in structure.custom_components:
            amount = calc(comp.comp_type, comp.value)
            custom_total += amount
            custom_items.append({
                'name'  : comp.name,
                'type'  : comp.comp_type,
                'value' : comp.value,
                'amount': amount
            })

    gross = round(
        earned_basic + da + hra + special +
        bonus + custom_total, 2
    )

    # EPF/PF
    if structure.epf_applicable:
        pf_employee = round(earned_basic * 0.12, 2)
        pf_employer = round(earned_basic * 0.13, 2)
    else:
        pf_employee = pf_employer = 0

    # ESIC
    if structure.esic_applicable:
        esic_employee = round(gross * 0.0075, 2)
        esic_employer = round(gross * 0.0325, 2)
    else:
        esic_employee = esic_employer = 0

    total_deductions = round(pf_employee + esic_employee, 2)
    net_pay          = round(gross - total_deductions, 2)

    return {
        'earned_basic'    : earned_basic,
        'da'              : da,
        'hra'             : hra,
        'special'         : special,
        'bonus'           : bonus,
        'custom_items'    : custom_items,
        'custom_total'    : custom_total,
        'gross'           : gross,
        'pf_employee'     : pf_employee,
        'esic_employee'   : esic_employee,
        'pf_employer'     : pf_employer,
        'esic_employer'   : esic_employer,
        'total_deductions': total_deductions,
        'net_pay'         : net_pay
    }


MONTH_DAYS = {
    1:31, 2:28, 3:31, 4:30,  5:31, 6:30,
    7:31, 8:31, 9:30, 10:31, 11:30, 12:31
}

MONTH_NAMES = {
    1:'January',   2:'February',  3:'March',
    4:'April',     5:'May',       6:'June',
    7:'July',      8:'August',    9:'September',
    10:'October',  11:'November', 12:'December'
}
