#!/usr/bin/env python

import csv
import collections
import pandas
import matplotlib.pyplot as plt
import numpy
import re
import json
import six

from math import *


# The coordinates of Weston VT:
weston_coords = ['-72.80', '43.28']

# The coordinates of Farm & Wilderness
f_w_coords = ['-72.73', '43.53']

# The distance from Weston VT to various cities
# Add a buffer of miles to ensure e.g., people *from* Boston don't get counted as
# coming from farther than boston
CITY_BUFFER = 10
to_greenfield = 50 + CITY_BUFFER
to_bos = 109 + CITY_BUFFER
to_nyc = 189.7 + CITY_BUFFER
to_chi = 761.4 + CITY_BUFFER
to_noatak = 3508.6 + CITY_BUFFER

# The years we are running this script for (exclusive on the high end):
YEARS = range(2009, 2018)

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
        float(row["lat"]), float(row["long"]),
        float(ydw_coords[1]), float(ydw_coords[0])
    )


def make_farther_than_chart(place_name, distance, filename, data):
    # Make farther than city counts for each year:
    farther_than_pct = {}

    for year in YEARS:
        # Number of people who traveled farther than NY divided by the number of people we have distance data for:
        farther_than_city = float(data[year][(data[year]['distance']>distance)]['distance'].count())
        total = float(data[year]['distance'].count())
        farther_than_pct[year] = (farther_than_city/total)*100
    farther_than_pct_series = pandas.Series(farther_than_pct)

    # Make a plot of it:
    plot = farther_than_pct_series.plot()
    fig = plot.get_figure()
    plt.title("Farther than {city}".format(city=place_name))
    plt.xlabel("Year")
    plt.ylabel("% of attendees from farther away than {city}".format(city=place_name))
    plt.axis([YEARS[0], YEARS[-1], 0, 100])
    plt.xticks(YEARS, [str(x) for x in YEARS])
    fig.savefig("results/{filename}.png".format(filename=filename))
    plt.close()


def main():

    # INITIAL PROCESSING
    # ==================

    data = {}
    for year in YEARS:
        # Read and process the CSV
        data[year] = pandas.read_csv("{}_long_lat.csv".format(year))
        # Add a column with the year label to the data:
        data[year]['year'] = year
        # Calculate the distances:
        data[year]['distance'] = data[year].apply(calculate_distance, axis=1)

    # Combine all the data:
    combined_data = pandas.concat(list(data.values()), ignore_index=True)

    # SUMMARIES
    # =========

    # Make a summary for each year:
    summaries = {}

    # Combine summaries for different years:
    for year in YEARS:
        summaries[year] = combined_data[(combined_data['year']==year)]['distance'].describe()
    summary_frame = pandas.concat(list(summaries.values()), axis=1, keys=YEARS)

    # Save the summaries to an HTML document:
    with open("results/results.html", "w+") as f:
        f.write(summary_frame.to_html())

    # Make a plot of the median and third quartile and save it to averages.png:
    plot = summary_frame['25%':'75%'].T.plot()
    fig = plot.get_figure()
    plt.title("Quartiles Distance From YDW")
    plt.xlabel("Year")
    plt.ylabel("Distance (Miles)")
    plt.axis([YEARS[0], YEARS[-1], 0, 400])
    plt.xticks(YEARS, [str(x) for x in YEARS])
    fig.savefig("results/averages.png")
    plt.close()

    # FARTHER THAN CHARTS
    # ===================
    make_farther_than_chart("Weston", 0, "farther_than_weston", data)
    make_farther_than_chart("NYC", to_nyc, "farther_than_nyc", data)
    make_farther_than_chart("Boston", to_bos, "farther_than_bos", data)
    make_farther_than_chart("Chicago", to_chi, "farther_than_chi", data)
    make_farther_than_chart("Greenfield", to_greenfield, "farther_than_greenfield", data)
    make_farther_than_chart("Noatak National Preserve (Alaska)", to_noatak, "farther_than_noatak", data)

    # GEOJSON FILES
    # =============

    # Save coords to GeoJSON files:
    for year in YEARS:
        featureCollection = {
            "type": "FeatureCollection",
        }

        features = [row[1:] for row in data[year].itertuples()]
        featureCollection["features"] = []
        # collections.Counter lets us cluster by zip code center
        for row, count in six.iteritems(collections.Counter(features)):
            # If no lat, do not include in GeoJSON file
            if pandas.isnull(row[0]):
                continue
            featureCollection['features'].append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": row[0:2],
                },
                "properties": {
                    "marker-symbol": count,
                    "title": "Distance: {} miles".format(row[3])
                }
            })

        with open("results/{}.geojson".format(year), "w+") as f:
            f.write(json.dumps(featureCollection))


if __name__ == "__main__":
    main()
