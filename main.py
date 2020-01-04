import json
import time
import datetime
import boto3
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# creating variables for pre-month and setting boto3 command for s3
today = datetime.date.today()
first = today.replace(day=1)
lastMonth = first - datetime.timedelta(days=1)
s3 = boto3.resource('s3')
client = boto3.client('s3')

def get_smbc_bill():

    options = Options()
    options.binary_location = '/opt/headless-chromium'
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--single-process')
    options.add_argument('--disable-dev-shm-usage')
    browser = webdriver.Chrome('/opt/chromedriver', chrome_options=options)
    browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': '/tmp/'}}
    command_result = browser.execute("send_command", params)

    # log-in of smbc bank portal site
    browser.get('https://direct.smbc.co.jp/aib/aibgsjsw5001.jsp')
    time.sleep(3)
    browser.find_element_by_id('S_BRANCH_CD').send_keys(os.environ['smbc_branch_no'])
    browser.find_element_by_id('S_ACCNT_NO').send_keys(os.environ['smbc_account_no'])
    browser.find_element_by_id('PASSWORD').send_keys(os.environ['smbc_password'])
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

    s3.meta.client.upload_file("/tmp/meisai.csv", os.environ['billing_bucket'], f"Billing/smbc/{lastMonth.year}/{lastMonth.strftime('%Y%m')}.csv")

def handler(event, context):

    get_smbc_bill()
    response = client.list_objects(Bucket=os.environ['billing_bucket'], Prefix=f"Billing/smbc/{lastMonth.year}/{lastMonth.strftime('%Y%m')}.csv")
    if response['Contents'][0]['ETag']:
        return {"statusCode": 200, "body": f"Billing/smbc/{lastMonth.year}/{lastMonth.strftime('%Y%m')}.csv upload successfully."}
    else:
        return {"statusCode": 0, "body": f"Billing/smbc/{lastMonth.year}/{lastMonth.strftime('%Y%m')}.csv upload failed."}
