#!/usr/bin/env python

import csv
import collections
import pandas
import matplotlib.pyplot as plt
import numpy
import re
import json

from math import *

# The coordinates of Weston VT:
weston_coords = ['-72.80', '43.28']

# The coordinates of Farm & Wilderness
f_w_coords = ['-72.73', '43.53']


def get_distance(lat_a, long_a, lat_b, long_b):
    "From http://zips.sourceforge.net/#dist_calc"
    distance = (sin(radians(lat_a)) *
          sin(radians(lat_b)) +
          cos(radians(lat_a)) *
          cos(radians(lat_b)) *
          cos(radians(long_a - long_b)))
    distance = (degrees(acos(distance))) * 69.09
    return distance


def calculate_distance(row):
    "Given a row with a `coords` column, calculate it's distance from Weston VT."
    if pandas.isnull(row["long"]) or pandas.isnull(row["lat"]):
        return None # No coords, short-circuit.

    ydw_coords = weston_coords if row['year'] in range(2011, 2015) else f_w_coords

    return get_distance(
        float(row["long"]), float(row["lat"]),
        float(ydw_coords[0]), float(ydw_coords[1])
    )


def main():
    data = {}
    for year in range(2009, 2015):
        # Read and process the CSV
        data[year] = pandas.read_csv("{}_long_lat.csv".format(year))
        # Add a column with the year label to the data:
        data[year]['year'] = year

    # Combine all the data:
    combined_data = pandas.concat(list(data.values()), ignore_index=True)

    # Calculate distances:
    combined_data['distance'] = combined_data.apply(calculate_distance, axis=1)

    # Make a summary for each year:
    summaries = {}

    # Print information for different years:
    for year in range(2009, 2015):
        summaries[year] = combined_data[(combined_data['year']==year)]['distance'].describe()
    summary_frame = pandas.concat(list(summaries.values()), axis=1, keys=range(2009, 2015))

    # Save coords to GeoJSON files:
    for year in range(2009, 2015):
        featureCollection = {
            "type": "FeatureCollection",
        }

        features = [row[1:4] for row in data[year].itertuples()]
        featureCollection["features"] = []
        for row in features:
            # If no lat, do not include in GeoJSON file
            if pandas.isnull(row[1]):
                continue
            featureCollection['features'].append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": row[0:2],
                },
                "properties": {
                }
            })

        with open("results/{}.geojson".format(year), "w+") as f:
            f.write(json.dumps(featureCollection))

    # Make a plot of the median and third quartile and save it to averages.png:
    plot = summary_frame['50%':'75%'].T.plot()
    fig = plot.get_figure()
    plt.title("2nd and 3rd Quartile Distance From YDW")
    plt.xlabel("Year")
    plt.ylabel("Distance (Miles)")
    plt.axis([2009, 2014, 0, 400])
    plt.xticks(range(2009, 2015), [str(x) for x in range(2009, 2015)])
    fig.savefig("results/averages.png")

    # Save the summaries to an HTML document:
    with open("results/results.html", "w+") as f:
        f.write(summary_frame.to_html())


if __name__ == "__main__":
    main()
