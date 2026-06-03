"""
Python script for crawling app information from the Google Play Store
"""
import csv
import requests

from bs4 import BeautifulSoup

"""
Definition of data positions in the csv files 
"""
NAME = 1
RATING = 4
DOWNLOADS = 5


"""
Method for crawling the Google Play Store for download numbers and user ratings of currently available apps
path_apps_query - Path to the file with Android package names to check
path_apps_crawl - Path to the file for the crawling results
"""
def inspectapps(path_apps_query, path_apps_crawl):
    app_link = "https://play.google.com/store/apps/details?id="
    with open(path_apps_crawl, 'w', newline='', encoding='utf-8') as csvw:
        writer = csv.writer(csvw)
        with open(path_apps_query, 'r', encoding='utf-8') as csvr:
            reader = csv.reader(csvr)
            row = 1
            try:
                for app in reader:
                    row += 1
                    if row % 10000 == 0:
                        print("=== Processed", row, "lines ===")
                    if 'sha256' in app:
                        print(app)
                        writer.writerow(app)
                        continue

                    # generate url, get html
                    url = app_link + app[NAME]
                    try:
                        request = requests.get(url)
                    except requests.exceptions.Timeout:
                        continue

                    if request.status_code != 404:
                        data = request.text
                        soup = BeautifulSoup(data, 'html.parser')
                        for i in soup.find_all("div", "ClM7O"):
                            if "Rat" in str(i):
                                app[RATING] = str(i).split("\"TT9eCd\">")[1].split("<")[0]
                            elif "img" in str(i):
                                continue
                            else:
                                app[DOWNLOADS] = str(i).split(">")[1].split("<")[0]
                        print(app)
                        writer.writerow(app)
            except Exception as e:
                print(e)


"""
Method for crawling the Google Play Store for the categories of apps of interest
path_apps_list - Path to the file with the candidates for validation
path_apps_category - Path to the file for the results
"""
def inspectappcategories(path_apps_list, path_apps_category):
    app_link = "https://play.google.com/store/apps/details?id="
    with open(path_apps_category, 'w', newline='', encoding='utf-8') as csvw:
        writer = csv.writer(csvw)
        with open(path_apps_list, 'r', encoding='utf-8') as csvr:
            reader = csv.reader(csvr)
            try:
                for app in reader:
                    print(app[0])
                    # generate url, get html
                    url = app_link + app[0]
                    request = requests.get(url)

                    category=""
                    if request.status_code != 404:
                        data = request.text
                        soup = BeautifulSoup(data, 'html.parser')
                        for i in soup.find_all("div"):
                            if "href=\"/store/apps/category/" in str(i):
                                category = str(i).split("category/")[1].split("\"")[0]
                        print(category)
                    writer.writerow([app[0], category])
            except Exception as e:
                print(e)


def main():
    inspectapps("../../Apps/DBResult.csv", "../../Apps/GPResult.csv")
    #inspectappcategories("../../Apps/Results/Candidate.csv", "../../Apps/Results/Categories.csv")


main()
