"""
Python script for using the APKPure API to crawl information for specific Android apps or to download the apps itself
"""
import csv
import time

from APKPureAPI import ApkPure

api = ApkPure()

# # Search for top result
#top_result = api.search_top("WhatsApp")
#print(top_result)
# #
# # Search for all results
#all_results = api.search_all("Tiktok")
#print(all_results)
# #
# # Get app versions
#versions = api.get_versions("WhatsApp")
#print(versions)
# #
# # Get app info
#app_info = api.get_info("WhatsApp")
#print(app_info)
# #
# # Download the newest version of an app
#results = api.download("apks", "WhatsApp")
#print(results)
# #
# # Download a specific version of an app
#results = api.download("apks", "com.edurev.class2", version="525", name_switch=True)
#print(results)
# #
# # Download specific versions of multiple apps
with open("Candidate2.csv", 'r', encoding='utf-8') as csvr:
    reader = csv.reader(csvr)
    head = next(reader)
    for line in reader:
        print(line)
        try:
            results = api.download("apks", line[0], version=line[1], name_switch=True)
            print(results)
        except Exception as e:
            print(e)
        time.sleep(3)
