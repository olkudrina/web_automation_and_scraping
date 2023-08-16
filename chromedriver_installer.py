import os
from zipfile import ZipFile
import requests
from bs4 import BeautifulSoup
from selenium import webdriver


class ChromeInstall():
    """Installing the compatible Chrome webdriver"""
    def __init__(self):
        self.chrome_version = self.get_current_chrome_version()

    def get_current_chrome_version(self):
        """
        Identify the location and then the Chrome version

        :return: string with current version of Chrome installed
        """
        stream = os.popen('reg query "HKLM\\SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Google Chrome"')
        output = stream.read()
        output = output.split('\n')

        chrome_version = [i for i in output if 'DisplayVersion' in i and 'REG_SZ' in i][0]
        chrome_version = chrome_version.strip().split(' ')[-1]

        return chrome_version

    def unzip_and_move(self, zip_file):
        """
        Unzip the acrhive with chromedriver and move the executable to cwd

        :param zip_file: the extracted archive with chromedriver in it
        :return: None
        """
        ver = self.chrome_version[:3]
        ZipFile(zip_file, 'r').extractall('./'+ver)
        # adding executable to the cwd
        try:
            os.rename('./'+ver+'/chromedriver-win64/chromedriver.exe', './chromedriver.exe')
        except FileExistsError:
            try:
                os.remove('./chromedriver.exe')
                os.rename('./'+ver+'/chromedriver-win64/chromedriver.exe', './chromedriver.exe')
            except PermissionError:
                print('Impossible to replace the file in cwd')

    def old_version_extract(self):
        """
        According to google guidelines, all versions up to 114 should be extracted
        using the installed Chrome version in the following way:
        -   First, find out which version of Chrome you are using;
        -   Take the Chrome version number, remove the last part, and append 
            the result to URL "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_";
        -   Use the URL created in the last step to retrieve a small file containing
            the version of ChromeDriver to use.
        
        https://chromedriver.chromium.org/downloads/version-selection
        :return: None
        """
        ver = '.'.join(self.chrome_version.split('.')[:-1])
        # define the latest release for the older version
        link_storage = 'https://chromedriver.storage.googleapis.com'
        link_release = link_storage+'/LATEST_RELEASE_'+ver
        latest_release = requests.get(link_release, timeout=30).text

        link_driver_32 = os.path.join(link_storage, latest_release, 'chromedriver_win32.zip')
        link_driver_64 = os.path.join(link_storage, latest_release, 'chromedriver_win64.zip')

        if requests.get(link_driver_64).status_code == 404:
            driver_file = requests.get(link_driver_32, stream=True, timeout=60)
        else:
            driver_file = requests.get(link_driver_64, stream=True, timeout=60)

        with open('chromedriver.zip', "wb") as arch:
            for chunk in driver_file.iter_content(chunk_size=512):
                if chunk:
                    arch.write(chunk)

    def new_version_extract(self):
        """
        According to google guidelines, new versions, starting from 115. are
        accessible through the accessibility tables:
        https://chromedriver.chromium.org/downloads/version-selection
        https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/115.0.5762.4/mac-x64/chromedriver-mac-x64.zip

        :return: None
        """
        ver = self.chrome_version
        all_versions = requests.get('https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json').json()['versions']
        comp_versions = [i for i in all_versions if i['version'][:10] == ver[:10]]
        link = [i['url'] for i in comp_versions[-1]['downloads']['chromedriver']
                if i['platform'] == 'win64'][0]
        driver_file = requests.get(link, stream=True, timeout=60)

        with open('chromedriver.zip', "wb") as arch:
            for chunk in driver_file.iter_content(chunk_size=512):
                if chunk:
                    arch.write(chunk)

    def stable_version_extract(self):
        """
        According to google guidelines, new versions, starting from 115. are
        accessible through the accessibility tables:
        https://chromedriver.chromium.org/downloads/version-selection
        https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/115.0.5762.4/mac-x64/chromedriver-mac-x64.zip

        This function will download the latest stable version of the driver
        :return: None
        """
        # ver = self.chrome_version[:4]
        # get all accessibility data for the latest stable releases
        stable_table_link = 'https://googlechromelabs.github.io/chrome-for-testing/#stable'
        stable_drivers = requests.get(stable_table_link)
        soup = BeautifulSoup(stable_drivers.text, 'html.parser')
        stable_elements = [el.text for el in soup.find_all('code')]
        # define the download link for the latest stable driver for current chrome version
        stable_driver = [i for i in stable_elements if ver in i
                        and 'chromedriver' in i
                        and 'win64' in i][0]

        stable_driver_file = requests.get(stable_driver, stream=True, timeout=60)

        with open('chromedriver.zip', "wb") as arch:
            for chunk in stable_driver_file.iter_content(chunk_size=512):
                if chunk:
                    arch.write(chunk)

    def get_driver(self):
        """
        Function to extract the chrome driver, that is compatible with the current chrome version

        :return: None
        """
        ver = self.chrome_version[:3]
        if int(ver) <= 114:
            self.old_version_extract()
        else:
            self.new_version_extract()

        self.unzip_and_move('chromedriver.zip')

    def check_driver(self):
        """
        Function to check whether there is already a compatible driver installed.
        If not - the driver is downloaded to cwd
        
        :return: None
        """
        try:
            options = webdriver.ChromeOptions()
            browser = webdriver.Chrome(options=options)
            browser.close()
        except:
            self.get_driver()

if __name__ == '__main__':
    try:
        options = webdriver.ChromeOptions()
        browser = webdriver.Chrome(options=options)
        browser.close()
    except:
        ChromeInstall().get_driver()
