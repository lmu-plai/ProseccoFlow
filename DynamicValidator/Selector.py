"""
Python script for selecting and downloading Android apps from the repository AndroZoo
"""
import multiprocessing
import os
import csv
import re
import time

from numerize import numerize
import requests

"""
Definition of data positions in the csv files, the variable for download retries and the AndroZoo API key
"""
SHA256 = 0
NAME = 1
RATING = 4
DOWNLOADS = 5

ti = 10
key = 'API key'


"""
Method for validating a downloaded Android package (APK)
apk - path to the APK
"""
def validateapk(apk):
    try:
        with open(apk, "rb") as file:
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            header = file.read(2)
            return file_size > 0 and header == b'PK'
    except:
        return False


"""
Method for downloading APKs from AndroZoo
apikey - the API key for AndroZoo
sha_hash - the SHA hash value of the APK to download
n - variable for retries
"""
def downloadapk(apikey, sha_hash, n):
    url = 'https://androzoo.uni.lu/api/download'
    params = {"apikey": apikey, "sha256": sha_hash}
    try:
        r = requests.get(url, params=params, timeout=60)
    except requests.exceptions.Timeout:
        return "Timeout"
    except requests.exceptions.RequestException as e:
        print(str(e))
        return None
    if r.status_code != 200 and n > 0:
        time.sleep(ti+1-n)
        return downloadapk(apikey, sha_hash, n-1)
    return r


"""
Method for processing and validating the APKs to download as well as checking for already existing files
sha_hash - the SHA hash value of the APK to download
package_name - package identifier of the Android app used for saving the file
path_apks - path to the directory for the APKs
path_processed_apks - path to the directory for analyzed APKs
download - control variable for downloading files 
"""
def checkapk(sha_hash, package_name, path_apks, path_processed_apks, download=False):
    file_name = f"{path_apks}/{package_name}.apk"
    processed_file_name = f"{path_processed_apks}/{package_name}.apk"
    if os.path.exists(processed_file_name) and validateapk(processed_file_name):
        print(f"{processed_file_name} is analyzed")
        return True
    if os.path.exists(file_name) and validateapk(file_name):
        print(f"{file_name} is valid")
        return True
    if os.path.exists(file_name):
        print(f"{file_name} is not valid")
        os.remove(file_name)
    if not download:
        return False
    print(f"Saving file {sha_hash}")
    r = downloadapk(key, sha_hash, ti)
    if r == "Timeout":
        print(f"Timeout: {file_name}")
        return False
    if r is None or r.status_code != 200:
        print(f"Failure: {file_name}, Status code: {r.status_code if r else 'Unknown'}")
        return False
    with open(file_name, "wb") as f:
        f.write(r.content)
    if validateapk(file_name):
        print(f"Success: {file_name}")
        return True
    else:
        print(f"{file_name} is not valid")
        os.remove(file_name)
        return False


"""
Method for initializing the download processes
lst - list of SHA hashes
chunk_size - count of elements in each process part
"""
def chunkapk(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


"""
Method for selecting relevant APKs based on download numbers and initializing the download
path_apps_query - path to the file with properties of the apps to download
path_apks - path to the directory for the APKs
path_processed_apks - path to the directory for analyzed APKs
"""
def selectapk(path_apps_query, path_apks, path_processed_apks):
    shas = []
    sha_package = {}
    with open(path_apps_query, 'r', encoding='utf-8') as csvd:
        reader = csv.reader(csvd)
        row = 1
        try:
            for app in reader:
                row += 1
                if 'sha256' in app:
                    continue
                sha_hash = app[SHA256]
                package_name = app[NAME]
                app_downloads = app[DOWNLOADS]
                if app_downloads == '':
                    app_downloads = '0+'
                if "+" not in app_downloads:
                    app_downloads = numerize.numerize(int(app_downloads))
                if re.search("[KMBT]", app_downloads):
                    shas.append(sha_hash)
                    sha_package[sha_hash] = package_name
        except Exception as e:
            print("Failed on line", app)
            print(e)
    print(f"{len(shas)} SHAs collected")
    chunk_size = 20
    sha_chunks = list(chunkapk(shas, chunk_size))
    for chuck_ind, sha_chunk in enumerate(sha_chunks):
        print(f"Processing {chuck_ind+1}/{len(sha_chunks)}")
        with multiprocessing.Pool(processes=20) as pool:
            results = pool.starmap(checkapk, [(sha, sha_package[sha], path_apks, path_processed_apks, True) for sha in sha_chunk])
        if not all(results):
            print(f"Errors in chunk {chuck_ind+1}")
        print(f"{chuck_ind+1}/{len(sha_chunks)} completed")


if __name__ == '__main__':
    multiprocessing.freeze_support()
    selectapk("../../Apps/GPResult.csv", "APK", "Cand")
