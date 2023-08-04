import os
import requests
from bs4 import BeautifulSoup
from zipfile import ZipFile


class ChromeInstall():
    def __init__(self):
        self.chrome_version = self.get_current_chrome_version()

    def get_current_chrome_version(self):
        """
        Identify the location and then the Chrome version

        :return: string with current version of Chrome installed
        """
        stream = os.popen('reg query "HKLM\\SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Google Chrome"')
        output = stream.read()

        chrome_version = ''
        for letter in output[output.rindex('DisplayVersion    REG_SZ') + 24:]:
            if letter != '\n':
                chrome_version += letter
            else:
                break
        chrome_version = chrome_version.strip()

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
        
        return None

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
        latest_release = requests.get(link_release).text

        link_driver_32 = os.path.join(link_storage, latest_release, 'chromedriver_win32.zip')
        link_driver_64 = os.path.join(link_storage, latest_release, 'chromedriver_win64.zip')
        
        if requests.get(link_driver_64).status_code == 404:
            driver_file = requests.get(link_driver_32, stream=True)
        else:
            driver_file = requests.get(link_driver_64, stream=True)
        
        with open('chromedriver.zip', "wb") as f:
            for chunk in driver_file.iter_content(chunk_size=512):
                if chunk:
                    f.write(chunk)

        return None

    def new_version_extract(self):
        """
        According to google guidelines, new versions, starting from 115. are
        accessible through the accessibility tables:
        https://chromedriver.chromium.org/downloads/version-selection
        :return: None
        """
        ver = self.chrome_version[:4]
        # get all accessibility data for the latest stable releases
        stable_drivers = requests.get('https://googlechromelabs.github.io/chrome-for-testing/#stable')
        soup = BeautifulSoup(stable_drivers.text, 'html.parser')
        stable_elements = [el.text for el in soup.find_all('code')]
        # define the download link for the latest stable driver for current chrome version
        stable_driver = [i for i in stable_elements if ver in i and 'chromedriver-win64' in i][0]

        stable_driver_file = requests.get(stable_driver, stream=True)

        with open('chromedriver.zip', "wb") as f:
            for chunk in stable_driver_file.iter_content(chunk_size=512):
                if chunk:
                    f.write(chunk)
        return None

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
        return None

if __name__ == '__main__':
    ChromeInstall().get_driver()
