import re


def clean_numbers(text):

    # split by comma, space, newline
    raw_numbers = re.split(r'[,\n\s]+', text.strip())

    total = len(raw_numbers)

    valid_numbers = []
    invalid_numbers = []
    seen = set()
    duplicate_count = 0

    for num in raw_numbers:

        num = num.strip()

        if not num:
            continue

        # check digits only
        if not num.isdigit():
            invalid_numbers.append(num)
            continue

        # check length
        if len(num) != 10:
            invalid_numbers.append(num)
            continue

        # must start 6-9
        if num[0] not in ['6','7','8','9']:
            invalid_numbers.append(num)
            continue

        # duplicate check
        if num in seen:
            duplicate_count += 1
            continue

        seen.add(num)
        valid_numbers.append(num)

    return {
        "total": total,
        "valid": valid_numbers,
        "invalid_count": len(invalid_numbers),
        "duplicate_count": duplicate_count
    }