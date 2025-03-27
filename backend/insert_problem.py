import csv
import sys
import os

# Dynamically adjust the module search path to include the backend directory
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from db import init_db, insert_problem  # Import directlyrefour

# Initialize the database
init_db()

# Parse the CSV data
# Assuming scraped_problems.csv is in the backend directory
csv_path = os.path.join(os.path.dirname(__file__), "scraped_problems.csv")
with open(csv_path, "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        title = row["Title"]
        url = row["URL"]
        # Extract problem_id (e.g., "1" from "1. Two Sum", "1Fill" from "1Fill")
        problem_id = title.split(".")[0] if "." in title else title
        insert_problem(problem_id, title, url)

print("Problems inserted successfully!")