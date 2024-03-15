import requests
import csv
import io

#write a code that makes a http get quest to the url and print the response

url = "http://gateway.premiumpatron.hu/v1/datacollector/arukereso/get_source_content?apikey=a5e3fTzJJcOU2DEevspm3RYTJP0Oalma"


response = requests.get(url)

# Assuming response.text contains the CSV data
csv_file = io.StringIO(response.text)



reader = csv.DictReader(csv_file, delimiter='\t')

# Remove leading and trailing spaces from field names
reader.fieldnames = [name.strip() for name in reader.fieldnames]

# Extract the links
links = []
for row in reader:
    link = row.get('Link')
    if link:
        links.append(link)
        print(f" here is a link:  {link}")
    prefered_link = row.get('Prefered Link')
    if prefered_link:
        links.append(prefered_link)
        print(f" here is a perefred link:  {prefered_link}")

# Print the links
for link in links:
    print(link)