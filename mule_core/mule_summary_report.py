import csv
import os
import re
from collections import Counter

def generate_report(csv_path="logs/mule_test_audit.csv"):
    if not os.path.exists(csv_path):
        print(f"❌ Error: {csv_path} not found.")
        return

    total_runs = 0
    passes = 0
    fails = 0
    missing_specialists = []

    with open(csv_path, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_runs += 1
            if row['Status'] == 'PASS':
                passes += 1
            else:
                fails += 1
                # Extract specialists from string: "Missing: ['PM', 'ME']"
                reason = row['Failure_Reason']
                found = re.findall(r"\'(\w+)\'", reason)
                missing_specialists.extend(found)

    # Calculate Stats
    success_rate = (passes / total_runs) * 100 if total_runs > 0 else 0
    failure_counts = Counter(missing_specialists)

    # Print Report
    print("="*40)
    print("      AEGIS GARDENER: TEST SUMMARY")
    print("="*40)
    print(f"Total Tests Run: {total_runs}")
    print(f"Success Rate:    {success_rate:.1f}% ({passes}/{total_runs})")
    print(f"Failure Rate:    {100-success_rate:.1f}% ({fails}/{total_runs})")
    print("-" * 40)
    print("TOP FAILING SPECIALISTS (Missing in Chain):")
    
    for role, count in failure_counts.most_common():
        percentage = (count / fails) * 100 if fails > 0 else 0
        print(f"- {role}: {count} occurrences ({percentage:.1f}% of failures)")
    
    print("="*40)

if __name__ == "__main__":
    generate_report()