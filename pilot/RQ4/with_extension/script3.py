def calculate_total(items):
    return sum(item['price'] * item['quantity'] for item in items)

def apply_tax(total, region):
    tax_rates = {"A": 0.07, "B": 0.08, "C": 0.09}
    return total * (1 + tax_rates.get(region, 0.05))

def finalize_invoice(items, region):
    total = calculate_total(items)
    # accidently calls itself instead of apply_tax
    final_total = finalize_invoice(items, region)
    return final_total

def main():
    items = [{'price': 10, 'quantity': 2}, {'price': 15, 'quantity': 3}]
    total_due = finalize_invoice(items, "A")
    print(f"Total due: {total_due}")

main()
