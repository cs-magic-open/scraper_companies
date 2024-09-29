import logging
import pathlib
import re
import time

import yaml
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from sqlmodel import SQLModel, Session, create_engine, select

from apps.scraper_companies.core.orm import Company


def is_document_idle():
    return driver.execute_script("return document.readyState") == "complete"


def parse_company():
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

    values = [find_next_td_content(key) for key in keys]
    table_dict = dict(zip(keys, values))
    url = driver.current_url
    id = re.search("https://www.qcc.com/firm/(.*?).html", url).group(1)
    name = driver.find_element(By.TAG_NAME, "h1").text
    data = {"id": id, "name": name, **table_dict}
    logging.info(data)
    return data


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
            logging.debug("检测到已存在的结果,等待它被移除并重新挂载")

            # 等待当前元素变为stale(被移除)
            WebDriverWait(driver, wait_ele).until(EC.staleness_of(first_result))
            logging.debug("现有结果已被移除")

        except:
            logging.debug("当前没有搜索结果,等待新结果出现")

        # 等待新的结果出现
        first_result = WebDriverWait(driver, wait_ele).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.list-group-item")))
        company_name = first_result.text
        logging.debug(f"访问公司: {company_name}")
        first_result.click()
        return company_name

    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    with open(pathlib.Path(__file__).parent / 'config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        company_names_to_search = config['companies']
        keys = [key.strip() for key in config['fields']['table']]

    logging.debug({"companies": company_names_to_search, "keys": keys})

    chrome_options = Options()

    # 除了在仓库本地新建用户目录之外
    # 也可以访问 chrome://version
    # 然后检查「个人资料路径」
    # 以我的为例：/Users/mark/Library/Application Support/Google/Chrome/Default
    # 最后的 Default 就是 profile 选项，前面部分是 user-data-dir
    # 使用这个路径可以复用各种插件之类
    # todo:更进一步深入研究
    chrome_options.add_argument(f"user-data-dir=out/chrome-user-data-dir")

    # 之所以不直接使用浏览器自带的 profile
    # 是因为 **Selenium 始终会创建一份临时拷贝的账户资料**
    # 导致无法持久化，从而每次都需要重新登录。
    # todo:更进一步深入研究
    # ---
    # 与其强行复用用户数据，不如直接创建一个干净的新的，专门用于自动化
    chrome_options.add_argument("profile-directory=Automation")

    driver = webdriver.Chrome(options=chrome_options)
    # 任意初始化一家公司网站
    driver.get('https://www.qcc.com/firm/85d0292125761b813b2408a8138f51ca.html')

    engine = create_engine("sqlite:///database.db")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for search_name in company_names_to_search:
            logging.info(f'parsing Company(search_name={search_name})')
            statement = select(Company).where(Company.search_name == search_name)
            result = session.exec(statement).first()
            if result:
                logging.warning("skipped")
            else:
                company_name = search_and_click_first_result(search_name)
                try:
                    data = parse_company()
                    model = Company(search_name=search_name, company_name=company_name, **data)
                    session.add(model)
                    logging.info("added")
                except Exception as e:
                    logging.error(f"An error occurred: {e}")
        session.commit()

    input("Press Enter to close the browser...")
