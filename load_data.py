import web_scraping as ws
import csv
import matplotlib.pyplot as plt
import numpy as np
import os
from textwrap import wrap

# matplotlib style
plt.style.use('fivethirtyeight')


# Load stats from file file of resident c_resid ("FOR", "NAT", "TOTAL"), country geo, for years in range of
# start_year and end_year
def load_stats(file, c_resid, geo, start_year, end_year):
    path_list = ws.spilt_filename(file)
    inp = open(path_list[0] + path_list[1] + ".csv", 'r')
    csv_inp = csv.DictReader(inp)
    for row in csv_inp:
        if row["c_resid"] == c_resid and row["geo"] == geo:
            # Do not forget that range counts from 0 (thus +1 is required if you need to get the last year)
            years = list(range(int(start_year), int(end_year + 1), 1))
            values = []
            for year in years:
                values.append(row[str(year)])
    res = Stats(years, values)
    return res


# Will save every stat for a specific topic of a certain country
class CountryStats:
    def __init__(self, country, file, start_year, end_year, description="You forgot description"):
        self.country = country
        self.description = description
        self.foreign = load_stats(file, "FOR", country, start_year, end_year)
        self.native = load_stats(file, "NAT", country, start_year, end_year)
        self.total = load_stats(file, "TOTAL", country, start_year, end_year)

    # Plots all the info the object contains into a bar graph
    def plot_me(self):
        # width of the whole group of bars
        width = 0.8
        # number of groups (of bars)
        num_bar = len(self.native.years)
        # create a linear space so I may plot a group on each point
        x = np.arange(num_bar)
        # customize the figure
        all_plot, ap = plt.subplots()
        all_plot.set_figheight(7)
        all_plot.set_figwidth(15)
        # plot the subplots (group of bars)
        ap.bar(x - width/3, self.native.get_int_values(), width=width/3, label="Natives")
        ap.bar(x,           self.foreign.get_int_values(), width=width/3, label="Foreigners")
        ap.bar(x + width/3, self.total.get_int_values(), width=width/3, label="Total")
        # labels - legend - title
        plt.xlabel("Year")
        plt.ylabel(f"Number of {self.description.split(' ')[0]} ")
        ap.legend()
        # HOW TO WRAP A BIG TITLE: https://stackoverflow.com/questions/10351565/how-do-i-fit-long-title
        plt.title("\n".join(wrap(f"{self.description} in {self.country}")))
        # set x ticks to be the linear space I created earlier
        ap.set_xticks(x)
        # change the values that are visible on the x axis of the plot
        ap.set_xticklabels(self.total.years)
        fig_path = "final_plots/"
        fig_name = self.country + '_' + self.description.split(" ")[0] + ".jpg"
        if os.path.exists(fig_path) == 0:
            os.mkdir(fig_path)
        plt.savefig(fig_path + fig_name)
        plt.close()

    # Function that saves the plots professor requested, using
    # options: "Natives", "Foreigners" or "Total"
    def request_plot(self, option):
        plt.figure(figsize=[14, 12])
        if option == "Natives":
            safe_obj = make_safe(self.native)
            plt.plot(safe_obj.years, safe_obj.get_int_values(), label="Natives")
        elif option == "Foreigners":
            safe_obj = make_safe(self.foreign)
            plt.plot(safe_obj.years, safe_obj.get_int_values(), label="Foreigners")
        elif option == "Total":
            safe_obj = make_safe(self.total)
            plt.plot(safe_obj.years, safe_obj.get_int_values(), label="Total")
        else:
            print("Not a valid input (func: plot_as_req)")
            exit(1)
        # fix x axis ticks
        plt.xticks(self.native.years, self.native.years)
        # labels - legend - title
        plt.xlabel("Year")
        plt.ylabel(f"Number of {self.description.split(' ')[0]} ")
        plt.legend()
        plt.title("\n".join(wrap(f"{self.description} in {self.country}")))
        # Save fig
        fig_path = "final_plots/"
        fig_name = self.country + '_' + self.description.split(" ")[0] + '_' + option + ".jpg"
        plt.savefig(fig_path + fig_name)
        plt.close()


# This function will clean the entire year from both the years list
# and the values list, of zero values, so the graphs are more accurate and don't have weird dips to 0
# The bar diagrams need to be of the same dimension, but on a certain year a country may have
# stats about foreigners and have none for natives. This means that the years I will try to plot on the same
# bar chart will differ. In order to make my life easier I will be using the function below, on demand, when
# I am about to plot the data into line charts
def make_safe(stats_obj):
    cnt = 0
    values = []
    years = []
    for value in stats_obj.values:
        if int(value) != 0:
            values.append(stats_obj.values[cnt])
            years.append(stats_obj.years[cnt])
        cnt += 1
    safe_obj = Stats(years, values)
    return safe_obj


# Save the years and the values of the given stats
# Will be used 3 times (foreign, native, total) in the CountryStats class
class Stats:
    def __init__(self, years, values):
        self.years = years
        self.values = self.make_safe(values)

    def get_int_values(self):
        res = [int(value) for value in self.values]
        return res

    def print_stats(self):
        print(f"Years: {self.years}")
        print(f"Values: {self.values}")

    # overrides the function above (an egrafes c++).
    # Some of the values in the csv file are ":", which means that there are no available data
    # In order to be able to plot countries that may have a column like that
    # I will make_safe the data, by replacing ":" with the integer 0
    def make_safe(self, values):
        cnt = 0
        ret = []
        for value in values:
            if value != ':':
                ret.append(value)
            else:
                ret.append(0)
            cnt += 1
        return ret
