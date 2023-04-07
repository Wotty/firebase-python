import requests
from bs4 import BeautifulSoup
import json

# Make a request to the website
url = "https://strengthlevel.com/strength-standards/male/kg"
response = requests.get(url)

# Parse the HTML content using Beautiful Soup
soup = BeautifulSoup(response.content, "html.parser")

# Find all the tables by bodyweight
tables = soup.find_all("table", class_="table is-striped is-fullwidth is-narrow")

# Create a dictionary to store the data
data = {}
counter = 0

# Loop through each table and extract the data
for table in tables:
    # Get the bodyweight for this table
    counter += 1
    bodyweight = f"Unknown {counter}"
    print(f"bodyweight: {bodyweight}")
    # Loop through each row in the table
    lift_data = []
    for row in table.find_all("tr"):
        # Extract the lift name, one rep max, and strength level for this row
        cells = row.find_all("td")
        if len(cells) > 0:
            lift = cells[0].text.strip()
            one_rep_max = cells[1].text.strip()
            strength_level = cells[2].text.strip()
            # Add the data for this lift to the list for this bodyweight
            lift_data.append(
                {
                    "lift": lift,
                    "one_rep_max": one_rep_max,
                    "strength_level": strength_level,
                }
            )
    # Add the data for this bodyweight to the dictionary
    data[bodyweight] = lift_data

# Save the data to a JSON file
with open("strength_data.json", "w") as outfile:
    json.dump(data, outfile)
