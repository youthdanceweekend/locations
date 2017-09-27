import csv
import zipcode

with open('2017_zip_codes.txt', 'r') as zip_code_file:
    with open('2017_long_lat.csv', 'w+') as csv_file:
        csvwriter = csv.writer(csv_file)
        csvwriter.writerow(['long', 'lat'])
        for line in zip_code_file:
            line = line.strip()
            zip_ = zipcode.isequal(line.strip().split('-')[0])
            if (zip_ is not None):
                csvwriter.writerow([zip_.lon, zip_.lat])
