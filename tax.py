import json
import os


class TaxInfo:
    def __init__(self, federal_tax, state_tax):
        self.federal_tax = federal_tax
        self.state_tax = state_tax

    def __str__(self):
        return f'federal: {self.federal_tax}\nstate: {self.state_tax}\n'


state_map = json.load(open('./states.json'))
federal_taxes = json.load(open('./data/2017/federal.json'))
state_data_dir = './data/2017/state/'
state_taxes = {}

for filename in os.listdir(state_data_dir):
    state_name = filename[:-5].replace('_', ' ')
    state_taxes[state_name] = json.load(open(state_data_dir + filename))


def abrev_to_name(abrev):
    return state_map[abrev.upper()].lower()


def bracket_percentage(income, brackets):
    if brackets is int:
        return brackets
    total = 0
    for i in range(1, len(brackets)):
        if brackets[i][0] > income:
            total += (income - brackets[i - 1][0]) * brackets[i - 1][1]
            return total / income
        else:
            total += (brackets[i][0] - brackets[i - 1][0]) * brackets[i - 1][1]
    return brackets[0][1]


def calc_fed_tax(income, marital_status, dependents):
    total = 0.0
    for category in ('medicare', 'socialSecurity', 'federalIncome'):
        if marital_status in federal_taxes['taxes'][category]['rate']:
            brackets = federal_taxes['taxes'][category]['rate'][marital_status]
        else:
            brackets = federal_taxes['taxes'][category]['rate']
        print(bracket_percentage(income, brackets))
        total += bracket_percentage(income, brackets)
    deductions = federal_taxes['taxes']['federalIncome']['deductions']
    std_deduct = deductions['standardDeduction']['amount'][marital_status]
    per_exempt = deductions['personalExemption']['amount']
    dep_exempt = deductions['dependents']['amount'] * dependents
    taxable_income = income - per_exempt - dep_exempt - std_deduct
    print(taxable_income, total)
    return max(0, total * taxable_income), \
           std_deduct + per_exempt + dep_exempt, \
           per_exempt + dep_exempt


def calc_state_tax(us_state, income, deductions, exemptions,
                   marital_status, dependents):
    total = 0.0
    neg = 0
    tax_info = state_taxes[us_state.upper()]['taxes']

    income_info = tax_info['income']
    if 'useFederalTaxableIncome' in income_info and \
            income_info['useFederalTaxableIncome']:
        income -= deductions
    elif 'useFederalAGI' in income_info and income_info['useFederalAGI']:
        income -= exemptions

    if income_info['rate'] is int:
        total += income_info['rate']
    else:
        if marital_status in income_info['rate']:
            brackets = income_info['rate'][marital_status]
        else:
            brackets = income_info['rate']
        total += bracket_percentage(income, brackets)

    deduct_info = income_info['deductions']
    std_deduct = deduct_info['standardDeduction']['amount'][marital_status]
    per_exempt = deduct_info['personalExemption']['amount'][marital_status]
    dep_exempt = deduct_info['dependents']['amount'] * dependents

    for category in ('disabilityInsurance',
                     'employmentSecurity',
                     'familyLeaveInsurance',
                     'mentalHealthServices',
                     'stateDisabilityInsurance',
                     'stateUnemploymentInsurance',
                     'unemploymentInsurance'):
        if category in tax_info:
            brackets = tax_info[category]['rate']
            if income > brackets[0][0]:
                neg += brackets[0][0] * brackets[0][1]
            else:
                total += brackets[0][1]

    taxable_income = income - per_exempt - dep_exempt - std_deduct
    return max(0, total * taxable_income + neg)


def calc_tax_info(us_state, income, marital_status='single', dependents=0):
    assert marital_status == 'single' or marital_status == 'married'
    us_state = us_state.upper()
    federal_tax, deductions, exemptions = calc_fed_tax(income, marital_status,
                                                       dependents)
    state_tax = calc_state_tax(us_state, income, deductions, exemptions,
                               marital_status, dependents)
    return TaxInfo(federal_tax, state_tax)


print(calc_tax_info('CA', 100000))
