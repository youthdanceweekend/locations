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

# The distance from Weston VT to various cities
to_bos = 109
to_nyc = 189.7
to_chi = 761.4


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


def make_farther_than_chart(place_name, distance, filename, data):
    # Make farther than city counts for each year:
    farther_than_pct = {}

    for year in range(2009, 2015):
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
    plt.axis([2009, 2014, 0, 100])
    plt.xticks(range(2009, 2015), [str(x) for x in range(2009, 2015)])
    fig.savefig("results/{filename}.png".format(filename=filename))
    plt.close()


def main():

    # INITIAL PROCESSING
    # ==================

    data = {}
    for year in range(2009, 2015):
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
    for year in range(2009, 2015):
        summaries[year] = combined_data[(combined_data['year']==year)]['distance'].describe()
    summary_frame = pandas.concat(list(summaries.values()), axis=1, keys=range(2009, 2015))

    # Save the summaries to an HTML document:
    with open("results/results.html", "w+") as f:
        f.write(summary_frame.to_html())

    # Make a plot of the median and third quartile and save it to averages.png:
    plot = summary_frame['50%':'75%'].T.plot()
    fig = plot.get_figure()
    plt.title("2nd and 3rd Quartile Distance From YDW")
    plt.xlabel("Year")
    plt.ylabel("Distance (Miles)")
    plt.axis([2009, 2014, 0, 400])
    plt.xticks(range(2009, 2015), [str(x) for x in range(2009, 2015)])
    fig.savefig("results/averages.png")
    plt.close()

    # FARTHER THAN CHARTS
    # ===================
    make_farther_than_chart("NYC", to_nyc, "farther_than_nyc", data)
    make_farther_than_chart("Boston", to_bos, "farther_than_bos", data)
    make_farther_than_chart("Chicago", to_chi, "farther_than_chi", data)

    # GEOJSON FILES
    # =============

    # Save coords to GeoJSON files:
    for year in range(2009, 2015):
        featureCollection = {
            "type": "FeatureCollection",
        }

        features = [row[1:4] for row in data[year].itertuples()]
        featureCollection["features"] = []
        # collections.Counter lets us cluster by zip code center
        for row, count in collections.Counter(features).iteritems():
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
                    "marker-symbol": count if count > 1 else None,
                }
            })

        with open("results/{}.geojson".format(year), "w+") as f:
            f.write(json.dumps(featureCollection))


if __name__ == "__main__":
    main()
