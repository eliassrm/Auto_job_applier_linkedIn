'''
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

Support me: https://github.com/sponsors/GodsScion

version:    26.01.20.5.08
'''

import socket

from modules.helpers import get_default_temp_profile, make_directories
from config.settings import run_in_background, stealth_mode, disable_extensions, safe_mode, keep_browser_open_on_exit, browser_debug_port, file_name, failed_file_name, logs_folder_path, generated_resume_path
from config.questions import default_resume_path
if stealth_mode:
    import undetected_chromedriver as uc
else: 
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    # from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from modules.helpers import find_default_profile_directory, critical_error_log, print_lg
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException

CHROME_DEBUG_HOST = "127.0.0.1"


def is_chrome_debugger_available(port: int) -> bool:
    try:
        with socket.create_connection((CHROME_DEBUG_HOST, port), timeout=0.5):
            return True
    except OSError:
        return False


def build_session(driver_options):
    if stealth_mode:
        print_lg("Downloading Chrome Driver... This may take some time. Undetected mode requires download every run!")
        driver = uc.Chrome(options=driver_options)
    else:
        driver = webdriver.Chrome(options=driver_options) #, service=Service(executable_path="C:\\Program Files\\Google\\Chrome\\chromedriver-win64\\chromedriver.exe"))
    driver.maximize_window()
    wait = WebDriverWait(driver, 5)
    actions = ActionChains(driver)
    return driver, actions, wait

def createChromeSession(isRetry: bool = False):
    make_directories([file_name,failed_file_name,logs_folder_path+"/screenshots",default_resume_path,generated_resume_path+"/temp"])
    if keep_browser_open_on_exit and not run_in_background and not stealth_mode and not isRetry and is_chrome_debugger_available(browser_debug_port):
        attached_options = Options()
        attached_options.add_experimental_option("debuggerAddress", f"{CHROME_DEBUG_HOST}:{browser_debug_port}")
        try:
            print_lg(f"Reconnecting to the existing Chrome window on {CHROME_DEBUG_HOST}:{browser_debug_port}.")
            driver, actions, wait = build_session(attached_options)
            return attached_options, driver, actions, wait
        except WebDriverException as e:
            print_lg("Found a Chrome debugging port but could not reconnect. Starting a new Chrome session.", e)

    # Set up WebDriver with Chrome Profile
    options = uc.ChromeOptions() if stealth_mode else Options()
    if run_in_background:   options.add_argument("--headless")
    if disable_extensions:  options.add_argument("--disable-extensions")
    if keep_browser_open_on_exit and not run_in_background:
        try:
            options.add_experimental_option("detach", True)
        except Exception as e:
            print_lg("Could not enable Chrome detach mode. Browser may still close when the bot exits.", e)
        if not stealth_mode:
            options.add_argument(f"--remote-debugging-address={CHROME_DEBUG_HOST}")
            options.add_argument(f"--remote-debugging-port={browser_debug_port}")

    print_lg("IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM! Or it's highly likely that application will just open browser and not do anything!")
    profile_dir = find_default_profile_directory()
    if isRetry:
        print_lg("Will login with a guest profile, browsing history will not be saved in the browser!")
    elif profile_dir and not safe_mode:
        options.add_argument(f"--user-data-dir={profile_dir}")
    else:
        print_lg("Logging in with a guest profile, Web history will not be saved!")
        temp_profile = get_default_temp_profile()
        if not temp_profile.startswith("--user-data-dir="):
            temp_profile = f"--user-data-dir={temp_profile}"
        options.add_argument(temp_profile)
    # try:
    #     driver = uc.Chrome(driver_executable_path="C:\\Program Files\\Google\\Chrome\\chromedriver-win64\\chromedriver.exe", options=options)
    # except (FileNotFoundError, PermissionError) as e:
    #     print_lg("(Undetected Mode) Got '{}' when using pre-installed ChromeDriver.".format(type(e).__name__))
    driver, actions, wait = build_session(options)
    return options, driver, actions, wait

try:
    options, driver, actions, wait = None, None, None, None
    options, driver, actions, wait = createChromeSession()
except SessionNotCreatedException as e:
    critical_error_log("Failed to create Chrome Session, retrying with guest profile", e)
    options, driver, actions, wait = createChromeSession(True)
except Exception as e:
    msg = 'Seems like Google Chrome is out dated. Update browser and try again! \n\n\nIf issue persists, try Safe Mode. Set, safe_mode = True in config.py \n\nPlease check GitHub discussions/support for solutions https://github.com/GodsScion/Auto_job_applier_linkedIn \n                                   OR \nReach out in discord ( https://discord.gg/fFp7uUzWCY )'
    if isinstance(e,TimeoutError): msg = "Couldn't download Chrome-driver. Set stealth_mode = False in config!"
    print_lg(msg)
    critical_error_log("In Opening Chrome", e)
    from pyautogui import alert
    alert(msg, "Error in opening chrome")
    try: driver.quit()
    except NameError: exit()
    
