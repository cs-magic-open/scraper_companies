import logging
import pathlib
import time

import yaml
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def is_document_idle():
    return driver.execute_script("return document.readyState") == "complete"


def find_next_td_content(text_a):
    # 使用XPath查找包含文本A的td元素
    xpath = f"//td[contains(., '{text_a}')]"

    try:
        # 等待元素出现
        td_element = (WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath))))

        # 获取下一个td元素
        next_td = td_element.find_element(By.XPATH, "following-sibling::td[1]")

        # 返回下一个td元素的文本内容
        return next_td.text

    except Exception as e:
        logging.error(f"Error: {e}")
        return None


def parse_company(driver):
    values = [find_next_td_content(key) for key in keys]
    table_dict = dict(zip(keys, values))
    result = {"url": driver.current_url, **table_dict}
    logging.info(result)
    return result


def search_and_click_first_result(text_a, wait_input=.5, wait_ele=3):
    try:
        # 找到搜索输入框并输入文本A
        search_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#searchKey")))
        search_input.click()
        time.sleep(wait_input)
        search_input.clear()
        time.sleep(wait_input)
        search_input.send_keys(text_a)
        # search_input.send_keys(Keys.RETURN) # 不需要回车，自动等待候选

        # 等待第一个结果出现或更新
        try:
            # 首先检查是否已存在结果
            first_result = driver.find_element(By.CSS_SELECTOR, "a.list-group-item")
            logging.info("检测到已存在的结果,等待它被移除并重新挂载")

            # 等待当前元素变为stale(被移除)
            WebDriverWait(driver, wait_ele).until(EC.staleness_of(first_result))
            logging.info("现有结果已被移除")

        except:
            logging.info("当前没有搜索结果,等待新结果出现")

        # 等待新的结果出现
        first_result = WebDriverWait(driver, wait_ele).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.list-group-item")))
        logging.info(f"新的搜索结果已出现: {first_result.text}")

        # 点击第一个结果
        first_result.click()
        logging.info("已点击第一个搜索结果")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    with open(pathlib.Path(__file__).parent / 'config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        companies = config['companies']
        keys = [key.strip() for key in config['fields']['table']]

    logging.info({"companies": companies, "keys": keys})

    chrome_options = Options()
    chrome_options.add_argument(f"user-data-dir=out/chrome-user-data-dir")
    chrome_options.add_argument("profile-directory=Automation")

    driver = webdriver.Chrome(options=chrome_options)
    # 任意初始化一家公司网站
    driver.get('https://www.qcc.com/firm/85d0292125761b813b2408a8138f51ca.html')

    for company_name in companies:
        logging.info(f'parsing Company(name={company_name})')
        search_and_click_first_result(company_name)
        parse_company(driver)

    input("Press Enter to close the browser...")
