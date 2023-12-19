# Starting:Common
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

# Starting:Chrome
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

options = webdriver.ChromeOptions()
# options.add_argument("--headless")
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
driver.set_window_size(width=800,height=600)

# Starting:Edge
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager

options = webdriver.EdgeOptions()
#options.add_argument("--headless")
driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=options)
driver.set_window_size(width=800,height=600)

# Ending:Common
driver.quit()

### ページのアクセス・内容抽出方法 ###

# ページを開く
driver.get("https://google.com")

# Google検索のようなテキストボックスに入力してEnter押してSubmitする場合
e = driver.find_element(By.XPATH, "//*[@id='aaaaa']")
e.send_keys("検索文字列など")
e.submit()

# ヒットしたすべての要素をリストで習得（aタグかつその属性hrefに"abc"を含む場合
elms = driver.find_elements(By.XPATH, "//@[contains(@href, 'abc']")

# 取得したURLを表示
for elm in elms:
    print("url: " + elm.get_attributes("href"))

# ホバーの一例
driver.get("https://www.amazon.co.jp/dp/B0CC5FW9C8?ref=KC_GS_GB_JP")
k = driver.find_element(By.XPATH, '//a[@id="nav-link-accountList"]')
actions = ActionChains(driver)
actions.move_to_element(k).perform()

# ユーザー名・パスワード入力する場合
e = driver.find_element(By.XPATH, "//*[@id='username']")
e.send_keys("user_name")
e = driver.find_element(By.XPATH, "//*[@id='password']")
e.send_keys("password")
e = driver.find_element(By.XPATH, "//*[text()='ログイン']")
e.click()

# チェックボックス(i)をチェックしたい場合(スクリプトのclickメソッドを呼び出したい場合）
#if not i.is_selected():
#    driver.execute_script("arguments[0].click();", i)

# JavaScriptのclickメソッド呼び出し例
d = driver.find_element(By.XPATH,'//button/*[@data-testid="DeleteOutlineOutlinedIcon"]/..')
driver.execute_script("arguments[0].click();", d)
y = driver.find_element(By.XPATH,'//button[text()="はい"]')
driver.execute_script("arguments[0].click();", y)

#要素から属性を取り出す場合
elm.get_attribute("href")

#要素からテキストを取り出す場合
elm.text



### その他
# 画面サイズ変更
driver.set_window_size(1600,10000)

# 画面キャプチャ
driver.save_screenshot('screenshot.png')


# 全部のHTMLソース内容を取得
# driver.page_source

# contentsのスクロール可能なサイズ分で画面キャプチャする
width = driver. execute_script(" return document. body. scrollWidth") 
height = driver. execute_script(" return document. body. scrollHeight") 
driver. set_window_size( width, height)
driver.save_screenshot("screenshot.png")

