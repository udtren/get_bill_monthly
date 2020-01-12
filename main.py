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
sns_client = boto3.client('sns')
ssm_client = boto3.client('ssm')
account_id = ssm_client.get_parameter(Name='account_id')

def get_smbc_bill():

    try:
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
        
        try:
            sns_client.publish(
                TopicArn=f"arn:aws:sns:ap-northeast-1:{account_id['Parameter']['Value']}:MyScheduleTask",
                Message="SUCCESS",
                Subject=f"{get_smbc_bill.__name__}() successed.",
                MessageAttributes={
                    'Author': {
                        'DataType': 'String',
                        'StringValue': 'Shinkai'
                    }
                }
            )
        except:
            sns_client.publish(
                TopicArn=f"arn:aws:sns:ap-northeast-1:{account_id['Parameter']['Value']}:MyScheduleTask",
                Message="FAIL_SNS",
                Subject=f"{get_smbc_bill.__name__}() successed but failed to send to sns.",
                MessageAttributes={
                    'Author': {
                        'DataType': 'String',
                        'StringValue': 'Shinkai'
                    }
                }
            )

    except:
        sns_client.publish(
            TopicArn=f"arn:aws:sns:ap-northeast-1:{account_id['Parameter']['Value']}:MyScheduleTask",
            Message="FAIL",
            Subject=f"{get_smbc_bill.__name__}() failed.",
            MessageAttributes={
                'Author': {
                    'DataType': 'String',
                    'StringValue': 'Shinkai'
                }
            }
        )

def handler(event, context):

    get_smbc_bill()
