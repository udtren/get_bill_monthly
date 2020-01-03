import os
import json
import time
import datetime
import boto3
from os import path
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

# creating variables for pre-month and setting boto3 command for s3
today = datetime.date.today()
first = today.replace(day=1)
lastMonth = first - datetime.timedelta(days=1)
s3 = boto3.resource('s3')
client = boto3.client('s3')

def get_smbc_bill(branch, account_no, password, download_path):

    # starting firefox with headless mode and disable download confirm
    options = Options()
    options.add_argument('-headless')
    fxProfile = webdriver.FirefoxProfile()
    fxProfile.set_preference("browser.download.folderList", 2)
    fxProfile.set_preference("browser.download.manager.showWhenStarting", 'false')
    fxProfile.set_preference("browser.download.dir", download_path)
    fxProfile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-csv")
    browser = webdriver.Firefox(firefox_profile=fxProfile, options=options)
    # log-in of smbc bank portal site
    browser.get('https://direct.smbc.co.jp/aib/aibgsjsw5001.jsp')
    time.sleep(3)
    browser.find_element_by_id('S_BRANCH_CD').send_keys(branch)
    browser.find_element_by_id('S_ACCNT_NO').send_keys(account_no)
    browser.find_element_by_id('PASSWORD').send_keys(password)
    browser.find_element_by_name('bLogon.y').click()

    # ignore the long-time password not change warning
    if len(browser.find_elements_by_id('agree')) > 0:
        checkbox = browser.find_element_by_id('agree')
        checkbox.click()
        browser.find_element_by_name('imgNext.y').click()

    browser.find_element_by_xpath('//a[@title="明細照会"]').click()

    # get the detail billing of pre-month and download the csv
    browser.find_element_by_name('web_zengetu').click()
    browser.find_element_by_id('DownloadCSV').click()
    browser.find_element_by_xpath('//a[text()="ログアウト"]').click()

    browser.quit()

with open('account_info.json') as f:
    data_ = f.read()
    data = json.loads(data_)

    # read the smbc account information of branch, account-number, password, where to save the csv file
    get_smbc_bill(branch=data['smbc'][0], account_no=data['smbc'][1], password=data['smbc'][2], download_path=data['smbc'][3])
    smbc_old_path = f"{data['smbc'][3]}\\meisai.csv"
    smbc_new_path = f"{data['smbc'][3]}\\{lastMonth.strftime('%Y%m')}.csv"
    # rename the csv file from 'meisai' to pre-month
    if path.exists(smbc_old_path):
        os.rename(smbc_old_path, smbc_new_path)
    # upload the csv to s3
    response = client.list_objects(Bucket=data['s3'], Prefix=f"Billing/smbc/{lastMonth.year}/{lastMonth.strftime('%Y%m')}.csv")
    if path.exists(smbc_new_path) and response['IsTruncated']==False:
        s3.meta.client.upload_file(smbc_new_path, data['s3'], f"Billing/smbc/{lastMonth.year}/{lastMonth.strftime('%Y%m')}.csv")

