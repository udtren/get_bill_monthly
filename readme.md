# Running headless chrome with selenium on AWS Lambda using python

三井住友銀行のWEBサイトから前月の明細CSVをダウンロードし、S3にアップロードする。  
AWS Lambda、Parameter store、CloudWatch Events、headless chrome、Pythonを使用。

reference link：  
https://github.com/yai333/Selenium-UI-testing-with-AWS-Lambda-Layers

```buildoutcfg
# download selenium
pip3 install -t seleniumLayer/selenium/python/lib/python3.7/site-packages selenium=2.37

# download chromedriver
cd seleniumLayer
mkdir chromedriver
cd chromedriver
curl -SL https://chromedriver.storage.googleapis.com/2.37/chromedriver_linux64.zip > chromedriver.zip
unzip chromedriver.zip
rm chromedriver.zip

# download chromebinary
curl -SL https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-41/stable-headless-chromium-amazonlinux-2017-03.zip > headless-chromium.zip
unzip headless-chromium.zip
rm headless-chromium.zip

# create lambda layer
zip –r chromedriver.zip chromedriver
zip –r selenium.zip selenium

# create lambda function, lambda layer, cloudwatch rule with cloudformation
```
