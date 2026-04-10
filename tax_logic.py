# tax_logic.py
from decimal import Decimal, ROUND_HALF_UP # Use Decimal for financial calculations

# --- EXAMPLE TAX DATA (Replace with accurate data for target year/country) ---
# --- Simplified US 2023 Data Example ---
TAX_YEAR = 2023

STANDARD_DEDUCTIONS = {
    "Single": Decimal("13850"),
    "MFJ": Decimal("27700"), # Married Filing Jointly
    "MFS": Decimal("13850"), # Married Filing Separately
    "HOH": Decimal("20800"), # Head of Household
    "QW": Decimal("27700"),  # Qualifying Widow(er)
}

TAX_BRACKETS = {
    "Single": [
        (Decimal("11000"), Decimal("0.10")),
        (Decimal("44725"), Decimal("0.12")),
        (Decimal("95375"), Decimal("0.22")),
        (Decimal("182100"), Decimal("0.24")),
        (Decimal("231250"), Decimal("0.32")),
        (Decimal("578125"), Decimal("0.35")),
        (Decimal("Infinity"), Decimal("0.37")) # Use large number or handle differently
    ],
     "MFJ": [ # Married Filing Jointly
        (Decimal("22000"), Decimal("0.10")),
        (Decimal("89450"), Decimal("0.12")),
        (Decimal("190750"), Decimal("0.22")),
        (Decimal("364200"), Decimal("0.24")),
        (Decimal("462500"), Decimal("0.32")),
        (Decimal("693750"), Decimal("0.35")),
        (Decimal("Infinity"), Decimal("0.37"))
    ],
    # !!! ADD BRACKETS FOR MFS, HOH, QW similarly !!!
    # Placeholder for others - YOU MUST ADD THESE
    "MFS": [ (Decimal("Infinity"), Decimal("0.37")) ], # Simplified - MUST BE REPLACED
    "HOH": [ (Decimal("Infinity"), Decimal("0.37")) ], # Simplified - MUST BE REPLACED
    "QW": [ (Decimal("Infinity"), Decimal("0.37")) ],  # Simplified - MUST BE REPLACED
}
# --- END EXAMPLE TAX DATA ---


def get_tax_data(year, filing_status):
    """
    Retrieves tax brackets and standard deduction for a given year and status.
    For this project, we only have one year's data hardcoded.
    """
    if year != TAX_YEAR:
        # In a real app, load data for the specific year
        raise ValueError(f"Tax data only available for year {TAX_YEAR}")

    if filing_status not in STANDARD_DEDUCTIONS or filing_status not in TAX_BRACKETS:
        raise ValueError(f"Invalid filing status provided: {filing_status}")

    return {
        "brackets": TAX_BRACKETS[filing_status],
        "standard_deduction": STANDARD_DEDUCTIONS[filing_status]
    }


def calculate_total_income(income_list):
    """Calculates total gross income from a list of income entries."""
    total = Decimal("0.00")
    if income_list:
        for entry in income_list:
            # Ensure amount is Decimal for precision
            total += Decimal(str(entry.get("amount", 0.0)))
    return total


def calculate_total_deductible_expenses(expense_list, deductions_credits_list=None):
    """
    Calculates total itemized deductions.
    Simplification: Assumes all logged 'expenses' are potentially itemizable deductions.
    A real app would need much more sophisticated logic based on categories.
    """
    total = Decimal("0.00")
    # Summing 'expenses' - Add more specific logic based on expense categories later
    if expense_list:
        for entry in expense_list:
             # Example: Only include specific categories if needed
             # if entry.get("category") in ["Medical", "MortgageInterest", "Charitable"]:
            total += Decimal(str(entry.get("amount", 0.0)))

    # Add specific deductions entered separately (if implemented)
    if deductions_credits_list:
         for entry in deductions_credits_list:
             if entry.get("type") == "deduction": # Assuming a 'type' field distinguishes
                 total += Decimal(str(entry.get("amount", 0.0)))

    return total

def calculate_taxable_income(gross_income, itemized_deductions, standard_deduction):
    """
    Calculates taxable income after choosing standard or itemized deduction.
    Handles potential negative income (sets taxable income to 0).
    """
    # Decide which deduction to use
    deduction_amount = max(itemized_deductions, standard_deduction)

    taxable = gross_income - deduction_amount
    return max(taxable, Decimal("0.00")) # Taxable income cannot be negative


def calculate_progressive_tax(taxable_income, brackets):
    """
    Calculates the total tax liability based on progressive tax brackets.
    Returns the total tax and a breakdown by bracket.
    """
    total_tax = Decimal("0.00")
    remaining_income = taxable_income
    last_bracket_limit = Decimal("0.00")
    tax_breakdown = [] # To store calculation for each bracket

    for limit, rate in brackets:
        limit_dec = Decimal(str(limit)) if limit != "Infinity" else Decimal('inf')
        rate_dec = Decimal(str(rate))

        # Amount of income taxable in this bracket
        taxable_in_bracket = max(Decimal("0.00"), min(remaining_income, limit_dec - last_bracket_limit))

        if taxable_in_bracket <= 0:
            break # No more income to tax

        tax_this_bracket = taxable_in_bracket * rate_dec
        total_tax += tax_this_bracket
        remaining_income -= taxable_in_bracket

        tax_breakdown.append({
            "limit": str(limit),
            "rate": f"{rate_dec * 100:.0f}%", # Format rate as percentage string
            "taxable_amount": taxable_in_bracket.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "tax_paid": tax_this_bracket.quantize(Decimal("0.01"), ROUND_HALF_UP)
        })

        last_bracket_limit = limit_dec

        if limit == "Infinity" or remaining_income <= 0:
            break # Handled all income or reached top bracket

    # Quantize final total tax to 2 decimal places
    total_tax = total_tax.quantize(Decimal("0.01"), ROUND_HALF_UP)
    return total_tax, tax_breakdown


def apply_credits(tax_liability, deductions_credits_list=None):
    """
    Applies tax credits (simplified).
    For now, just subtracts total credit amount. Real credits have complex rules.
    """
    total_credits = Decimal("0.00")
    if deductions_credits_list:
        for entry in deductions_credits_list:
            if entry.get("type") == "credit": # Check the type
                total_credits += Decimal(str(entry.get("amount", 0.0)))

    # Tax liability cannot go below zero due to most credits (check specific rules)
    final_tax = max(Decimal("0.00"), tax_liability - total_credits)
    return final_tax, total_credits

# --- Main Calculation Function ---
def calculate_full_taxes(user_financial_data, filing_status, year):
    """
    Orchestrates the entire tax calculation process for a given year.
    Returns a dictionary with summary results.
    """
    results = {
        "year": year,
        "filing_status": filing_status,
        "error": None,
        "gross_income": Decimal("0.00"),
        "itemized_deductions": Decimal("0.00"),
        "standard_deduction": Decimal("0.00"),
        "chosen_deduction": Decimal("0.00"),
        "taxable_income": Decimal("0.00"),
        "calculated_tax": Decimal("0.00"), # Before credits
        "tax_breakdown": [],
        "total_credits": Decimal("0.00"),
        "final_tax_liability": Decimal("0.00") # After credits
    }

    year_str = str(year)

    # 1. Get year-specific tax data (brackets, std deduction)
    try:
        tax_data = get_tax_data(year, filing_status)
        results["standard_deduction"] = tax_data["standard_deduction"]
    except ValueError as e:
        results["error"] = str(e)
        return results # Cannot proceed without tax data

    # 2. Get financial data for the year
    financials_for_year = user_financial_data.get(year_str, {})
    income_list = financials_for_year.get("income", [])
    expense_list = financials_for_year.get("expenses", [])
    # Assume deductions/credits are stored here eventually
    deductions_credits_list = financials_for_year.get("deductions_credits", [])

    # 3. Calculate Totals
    results["gross_income"] = calculate_total_income(income_list)
    # Pass both expenses and deductions/credits for calculation
    results["itemized_deductions"] = calculate_total_deductible_expenses(expense_list, deductions_credits_list)

    # 4. Calculate Taxable Income
    results["chosen_deduction"] = max(results["itemized_deductions"], results["standard_deduction"])
    results["taxable_income"] = calculate_taxable_income(
        results["gross_income"],
        results["itemized_deductions"],
        results["standard_deduction"]
    )

    # 5. Calculate Tax Liability (Progressive)
    results["calculated_tax"], results["tax_breakdown"] = calculate_progressive_tax(
        results["taxable_income"],
        tax_data["brackets"]
    )

    # 6. Apply Credits
    results["final_tax_liability"], results["total_credits"] = apply_credits(
        results["calculated_tax"],
        deductions_credits_list # Pass the list here
    )

    return results