import csv
import json

rows_read = 0
rows_kept = []
seen_emails = set()
rows_rejected = 0
people_per_city = {}
name_email_pairs = []
reject_reasons_rows = []
reject_reasons = {}
duplicates_found = 0

with open("warmup-data/people.csv", newline='') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        rows_read += 1

        name = row["name"].strip()
        email = row["email"].strip().lower()
        city = row["city"].strip()
        age = row["age"].strip()

        # if email not in seen_emails:
        seen_emails.add(email)

        if not name:
            rows_rejected += 1
            reject_reasons_rows.append((row, "empty name"))
            if "empty name" in reject_reasons:
                reject_reasons["empty name"] += 1
            else:
                reject_reasons["empty name"] = 1

        if not age.isdigit():
            rows_rejected += 1
            reject_reasons_rows.append((row, "age not a number"))
            if "age not a number" in reject_reasons:
                reject_reasons["age not a number"] += 1
            else:
                reject_reasons["age not a number"] = 1
            continue

        elif not 18 <= int(age) <= 120:
            rows_rejected += 1
            reject_reasons_rows.append((row, "age out of range"))
            if "age out of range" in reject_reasons:
                reject_reasons["age out of range"] += 1
                continue
            reject_reasons["age out of range"] = 1

        if not city:
            city = "unknown"
            row["city"] = city

        name_email_pairs.append((name, email))
        if city in people_per_city:
            people_per_city[city] += 1

        else:
            people_per_city[city] = 1

        rows_kept.append(row)

summary = {
    "rows_read": rows_read,
    "rows_kept": len(rows_kept),
    "rows_rejected": rows_rejected,
    "duplicates_found": rows_read - len(seen_emails),
    "reject_reasons": {
        "empty name": reject_reasons["empty name"],
        "age not a number": reject_reasons["age not a number"],
        "age out of range": reject_reasons["age out of range"],
    },
    "cities_count": len(people_per_city),
    "people_per_city": dict(sorted(people_per_city.items()))
}

with open("summary.json", "w") as output:
    json.dump(summary, output, indent=2)
