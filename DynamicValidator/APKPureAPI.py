"""
Python script for crawling the alternative Android app store APKPure for information and apps
"""
import json
import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import re
import sys
import cloudscraper


class ApkPure:
    """
    Initialization method for connection to the app store
    headers - custom headers
    """
    def __init__(self, headers: dict | None = None) -> None:
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15"
            }
        self.headers = headers
        self.query_url = "https://apkpure.com/search?q="

    """
    Initialization method for app search
    name - app name
    """
    def check_name(self, name):
        name = name.strip()
        if not name:
            sys.exit(
                "No search query provided!",
            )

    """
    Method for processing the web page of the app store
    url - Uniform Resource Locator of the web page
    """
    def __helper(self, url) -> BeautifulSoup:
        response = self.get_response(url=url)
        # Since response could be None check and try again if it is
        if not response:
            return self.__helper(url)
        return BeautifulSoup(response.text, "html.parser")

    """
    Method for connecting to the wep page of the app store
    url - Uniform Resource Locator of the web page
    kwargs - keyword arguments
    """
    def get_response(self, url: str, **kwargs) -> requests.Response | None:
        response = requests.get(url, self.headers)

        if response.status_code == 403:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url=url, **kwargs)

        # Return the response if the response is successful i.e status_code == 200
        return response if response.status_code == 200 else None

    """
    Method for extracting the app information
    Basic information: App name, Developer
    Package URL: Link to wep page of the app
    Icon: App icon
    Package data: Package name, File size, Package version
    Download link: Link to download the app
    html_element - HTML code of the web page
    """
    def extract_info_from_search(self, html_element):
        def get_basic_info() -> dict:
            title = html_element.find("p", class_="p1")
            developer = html_element.find("p", class_="p2")
            return {
                "title": title.text.strip() if title else "Unknown",
                "developer": developer.text.strip() if developer else "Unknown",
            }

        def get_package_url(html_element) -> dict:
            package_url = html_element.find("a")
            return {"package_url": package_url.get("href", "Unknown")}

        def get_icon() -> dict:
            icon = html_element.find("img")
            return {"icon": icon.attrs.get("src", "Unknown") if icon else "Unknown"}

        def get_package_data() -> dict:
            package_data = html_element.find("a", class_="is-download")

            if package_data is not None:
                if not package_data.get("data-dt-app"):
                    package_data = html_element

                package_name = package_data.get("data-dt-app")
                package_size = package_data.get("data-dt-filesize")
                package_version = package_data.get("data-dt-version")
                package_version_code = package_data.get("data-dt-versioncode")

                return {
                    "package_name": package_name,
                    "package_size": package_size,
                    "package_version": package_version,
                    "package_version_code": package_version_code,
                }
            else:
                return {
                    "package_information": "Not available",
                }

        def get_download_link() -> dict:
            if download_link := html_element.find("a", class_="is-download"):
                return {"download_link": download_link.attrs.get("href", "Unknown")}
            else:
                return {"download_link": "Not available"}

        basic_info: dict = get_basic_info()
        package_url: dict = get_package_url(html_element)
        icon: dict = get_icon()
        package_data: dict = get_package_data()
        download_link: dict = get_download_link()

        # Spread all the info into the all_info and then dump it to json
        all_app_info = basic_info | icon | package_data | download_link | package_url

        return all_app_info

    """
    Method to search for the app name and evaluate the first search result
    name - app name
    """
    def search_top(self, name: str) -> str | Exception:
        self.check_name(name)

        query_url = self.query_url + name
        soup_obj = self.__helper(query_url)

        # The div element
        first_div: BeautifulSoup = soup_obj.find("div", class_="first brand is-brand sa-all-div sa-apps-div")

        if first_div is None:
            list_of_apps = soup_obj.find("ul", id="search-res")  # UL
            top_app_in_list_of_apps = list_of_apps.find("li")  # LI
            result = self.extract_info_from_search(top_app_in_list_of_apps)
        else:
            result = self.extract_info_from_search(first_div)
        return json.dumps(result)

    """
    Method to search for the app name and evaluate all search results
    name - app name
    """
    def search_all(self, name: str) -> str:
        self.check_name(name)

        url = self.query_url + name
        soup = self.__helper(url)

        first_app = soup.find("div", class_="first brand is-brand sa-all-div sa-apps-div")

        list_of_apps = soup.find("ul", id="search-res")  # UL
        apps_in_list_of_apps = list_of_apps.find_all("li")  # LI's

        all_results = [self.extract_info_from_search(first_app)]

        for app in apps_in_list_of_apps:
            all_results.append(self.extract_info_from_search(app))
        return json.dumps(all_results)

    """
    Method to crawl for available versions of the app and extract the download link
    name - app name
    """
    def get_versions(self, name) -> str:
        s = json.loads(self.search_top(name))
        url = f"{s["package_url"]}/versions"
        soup = self.__helper(url)

        if 'package_name' in s.keys():
            full = [{"app": s["package_name"]}]
        else:
            package_name = s["package_url"].rsplit("/", 1)[1]
            full = [{"app": package_name}]
        ul = soup.find("ul", class_="ver-wrap")
        lists = ul.find_all("li")
        lists.pop()
        for li in lists:
            dl_btn = li.find("a", class_="ver_download_link").attrs
            package_version = dl_btn["data-dt-version"]
            download_link = dl_btn["href"]

            package_versioncode = dl_btn["data-dt-versioncode"]

            new = {
                "version": package_version,
                "download_link": download_link,
                "version_code": package_versioncode,
            }
            full.append(new)
        return json.dumps(full)

    """
    Method to extract the complete set of information for an app including name, versions, description, etc.
    name - app name
    """
    def get_info(self, name: str) -> str:
        url = json.loads(self.search_top(name))["package_url"]
        html_obj = self.__helper(url)

        divs = html_obj.find("div", class_="detail_banner")
        title = divs.find("div", class_="title_link").get_text(strip=True)
        header = []
        for obj in divs.find_all("div", class_="head"):
            header.append(obj.get_text(strip=True))

        sdk_info = divs.find("p", class_="details_sdk")
        developer = sdk_info.find("a").get_text(strip=True)
        latest_version = divs.find("p", class_="version-name").get_text(strip=True)

        dl_btn = divs.find("a", class_="download_apk_news").attrs
        package_name = dl_btn["data-dt-package_name"]
        package_versioncode = dl_btn["data-dt-version_code"]
        download_link = dl_btn["href"]

        # Find the Description
        print(html_obj)
        description = html_obj.find("div", class_="translate-content").get_text()

        # Older Versions
        versions = json.loads(self.get_versions(name))
        new = {
            "title": title,
            "rating": header[0],
            "date": header[1],
            "Android": header[2],
            "latest_version": latest_version,
            "description": description,
            "developer": developer,
            "package_name": package_name,
            "package_versioncode": package_versioncode,
            "package_url": download_link,
            "older_versions": versions,
        }
        return json.dumps(new)

    """
    Method for initializing the download of specific versions of an app
    file_path - path for the downloaded files
    name - name for saving the downloaded file
    version - app version to download
    name_switch - switch to change the name of the downloaded app file  
    """
    def download(self, file_path: str, name: str, version: str = "", name_switch: bool = False) -> str | None:
        versions = json.loads(self.get_versions(name))
        url_part = ""
        if not version:
            url_part = f"{versions[0]["app"]}?versionCode={versions[1]["version_code"]}"

        for v in versions[1:]:
            if version == v["version"] or version == v["version_code"]:
                url_part = f"{versions[0]["app"]}?versionCode={v["version_code"]}"
                break

        if not url_part:
            print(f"Invalid Version: {version}")
            return None
        if name_switch:
            return self.downloader(url_part, file_path, name)
        return self.downloader(url_part, file_path)

    """
    Method for downloading apps
    url_part - url part containing the version information
    file_path - path for the downloaded files
    name - name for saving the downloaded file, if name_switch is activated (see download method)
    """
    def downloader(self, url_part: str, file_path:str, name: str = "") -> str:
        base_url_xapk = "https://d.apkpure.com/b/XAPK/"
        base_url_apk = "https://d.apkpure.com/b/APK/"
        url = base_url_xapk + url_part
        apk_switch = True
        response = self.get_response(
            url=url, stream=True, allow_redirects=True, headers=self.headers
        )
        d = response.headers.get("content-disposition")
        if d is None:
            url = base_url_apk + url_part
            apk_switch = False
            response = self.get_response(
                url=url, stream=True, allow_redirects=True, headers=self.headers
            )
            d = response.headers.get("content-disposition")
        if name:
            if apk_switch:
                fname = os.path.join(os.getcwd(), f"{file_path}/{name}.xapk")
            else:
                fname = os.path.join(os.getcwd(), f"{file_path}/{name}.apk")
        else:
            fname = re.findall("filename=(.+)", d)[0].strip('"')
            fname = os.path.join(os.getcwd(), f"{file_path}/{fname}")

        os.makedirs(os.path.dirname(fname), exist_ok=True)

        if os.path.exists(fname) and int(response.headers.get("content-length", 0)) == os.path.getsize(fname):
            print("File exists!")
            return os.path.realpath(fname)

        with tqdm.wrapattr(
            open(fname, "wb"),
            "write",
            miniters=1,
            total=int(response.headers.get("content-length", 0)),
        ) as file:
            for chunk in response.iter_content(chunk_size=4 * 1024):
                if chunk:
                    file.write(chunk)

        return os.path.realpath(fname)
