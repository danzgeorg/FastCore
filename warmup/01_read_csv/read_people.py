import csv
import json

rows_read = 0
rows_kept = []
seen_emails = set()
people_per_city = {}
name_email_pairs = []
reject_reasons_rows = []
reject_reasons = {}
duplicates_found = 0
people_csv = "../../warmup-data/people.csv"
summary_json = "../../warmup/01_read_csv/summary.json"

with open(people_csv, newline='') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        rows_read += 1

        name = row["name"].strip()
        email = row["email"].strip().lower()
        city = row["city"].strip()
        age = row["age"].strip()

        if email in seen_emails:
            continue
        seen_emails.add(email)

        if not name:
            reject_reasons_rows.append((row, "empty name"))
            if "empty name" in reject_reasons:
                reject_reasons["empty name"] += 1
            else:
                reject_reasons["empty name"] = 1
            continue

        try:
            age = int(age)
        except ValueError:
            reject_reasons_rows.append((row, "age not a number"))
            if "age not a number" in reject_reasons:
                reject_reasons["age not a number"] += 1
            else:
                reject_reasons["age not a number"] = 1
            continue
        else:
            if not 18 <= age <= 120:
                reject_reasons_rows.append((row, "age out of range"))
                if "age out of range" in reject_reasons:
                    reject_reasons["age out of range"] += 1
                else:
                    reject_reasons["age out of range"] = 1
                continue

            if not city:
                city = "unknown"
                row["city"] = city
            name_email_pairs.append((name, email))
            if city in people_per_city:
                people_per_city[city] += 1
            else:
                people_per_city[city] = 1
            rows_kept.append(row)

duplicates = rows_read - len(seen_emails)
rows_rejected = sum(reject_reasons.values())
kept = rows_read - duplicates - rows_rejected

summary = {
    "rows_read": rows_read,
    "rows_kept": kept,
    "rows_rejected": rows_rejected,
    "duplicates_found": duplicates,
    "reject_reasons": {
        "empty name": reject_reasons["empty name"],
        "age not a number": reject_reasons["age not a number"],
        "age out of range": reject_reasons["age out of range"],
    },
    "cities_count": len(people_per_city),
    "people_per_city": dict(sorted(people_per_city.items()))
}

with open(summary_json, "w") as output:
    json.dump(summary, output, indent=2)
