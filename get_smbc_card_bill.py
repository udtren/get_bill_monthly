import time
import datetime
import boto3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

today = datetime.date.today()
s3 = boto3.resource('s3')
ssm_client = boto3.client('ssm')
sns_client = boto3.client('sns')

driver_path = "C:\\Users\\udtre\\Documents\\geckodriver\\chromedriver.exe"
download_path = "C:\\Users\\udtre\\Documents\\Billing\\smbc-card"
chrome_profile = "C:\\Users\\udtre\\AppData\\Local\Google\\Chrome\\User Data\\Default"
login_id = ssm_client.get_parameter(Name='smbc_card_login_id')
login_pw = ssm_client.get_parameter(Name='smbc_card_login_pw')
billing_bucket = ssm_client.get_parameter(Name='billing_bucket')
account_id = ssm_client.get_parameter(Name='account_id')


def get_smbc_card_bill():

    try:
        options = Options()
        options.add_argument("user-data-dir=C:\\Users\\udtre\\AppData\\Local\Google\\Chrome\\User Data")
        options.add_argument('--headless')

        browser = webdriver.Chrome(driver_path, options=options)

        browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_path}}
        command_result = browser.execute("send_command", params)

        browser.get('https://www.smbc-card.com/mem/index.jsp')

        time.sleep(1)
        browser.find_element_by_xpath('//*[@id="contWrap"]/div[3]/div/ul[1]/li/div[2]/form/ul/li[1]/input').send_keys(login_id['Parameter']['Value'])
        browser.find_element_by_xpath('//*[@id="contWrap"]/div[3]/div/ul[1]/li/div[2]/form/ul/li[2]/input').send_keys(login_pw['Parameter']['Value'])
        browser.find_element_by_xpath('//*[@id="contWrap"]/div[3]/div/ul[1]/li/div[2]/form/p/input').click()
        time.sleep(3)
        browser.find_element_by_xpath('//*[@id="vp-view-WebApiId_U000100_9"]').click()
        time.sleep(3)
        browser.find_element_by_xpath('//*[@id="vp-view-VC0502-003_RS0001_U051111_3"]').click()
        browser.find_element_by_id('sideVpassLogoutBtn').click()

        file_path = f"{download_path}\\{today.year}{today.month:02d}.csv"
        s3.meta.client.upload_file(file_path, billing_bucket['Parameter']['Value'], f"Billing/smbc-card/{today.year}/{today.year}{today.month:02d}.csv")
        try:
            sns_client.publish(
                TopicArn=f"arn:aws:sns:ap-northeast-1:{account_id['Parameter']['Value']}:MyScheduleTask",
                Message="SUCCESS",
                Subject=f"{get_smbc_card_bill.__name__}() successed.",
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
                Subject=f"{get_smbc_card_bill.__name__}() successed but failed to send to sns.",
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
            Subject=f"{get_smbc_card_bill.__name__}() failed.",
            MessageAttributes={
                'Author': {
                    'DataType': 'String',
                    'StringValue': 'Shinkai'
                }
            }
        )

get_smbc_card_bill()


