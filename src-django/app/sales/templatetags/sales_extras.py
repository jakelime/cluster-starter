from datetime import date, datetime
from django import template

register = template.Library()

# Fields to format as Currency ($1,234.56)
CURRENCY_FIELDS = {
    "est_sales_us",
    "fct_sales_value",
    "actual_sales_value",
    "fct_cost",
    "actual_cost",
    "fct_gp",
    "actual_gp",
    "poc_cost_mark_up",
    "poc_sales_b_f",
    "poc_cost_b_f",
}

# Fields to format as Percentage (0.12 -> 12.00%)
PERCENTAGE_FIELDS = {
    "approved_gp_during_bid",
    "gp_percent",
    "poc",
}

def should_redact(request):
    """
    Helper to determine if financials should be redacted.
    1. Redact if user lacks permission 'sales.view_financials' (Change permission codename as needed).
    2. Redact if session variable 'hide_financials' is True.
    """
    # Check Permission (Adjust 'sales.view_financials' to your actual permission)
    if not request.user.has_perm('sales.view_financials') and not request.user.is_superuser:
        return True

    # Check Presentation Mode Toggle
    return request.session.get("hide_financials", False)

@register.filter
def format_field_value(bound_field, request=None):
    """
    Formats a form field's value for display based on its name and type,
    mimicking the logic in SalesTable.
    """
    value = bound_field.value()

    if value in (None, ""):
        return "-"

    name = bound_field.name

    try:
        # Handle Dates (Match table format: Y-m-d)
        if isinstance(value, (date, datetime)):
            return value.strftime("%Y-%m-%d")

        # Handle Currency
        if name in CURRENCY_FIELDS:
            if not request or should_redact(request):
                return "$XXX.XX"
            # Convert string to float if necessary (e.g. from bound form error)
            val = float(value)
            return f"${val:,.2f}"

        # Handle Percentage
        if name in PERCENTAGE_FIELDS:
            val = float(value)
            return f"{val * 100:.2f}%"

    except (ValueError, TypeError):
        # Fallback for conversion errors, return raw string
        pass

    return value