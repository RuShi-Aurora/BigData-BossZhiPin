import os
import time
import random
import json
from datetime import datetime
import traceback
import re
from urllib.parse import quote
import logging
#D:\BigData\drivers\msedgedriver.exe
# 处理Selenium依赖项
try:
    from selenium import webdriver
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    from selenium.webdriver.common.keys import Keys
    
    # 尝试导入webdriver_manager，如果失败则不使用
    try:
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        USE_WEBDRIVER_MANAGER = True
    except ImportError:
        USE_WEBDRIVER_MANAGER = False
        print("webdriver_manager 未安装，将使用本地EdgeDriver")
except ImportError:
    print("错误: 请先安装Selenium: pip install selenium")
    print("如需自动管理EdgeDriver，请安装: pip install webdriver-manager")
    exit(1)

# 导入数据管理器类
try:
    from data_manager import DataManager
except ImportError:
    print("警告: 无法导入DataManager，将创建简化版数据管理")
    
    # 简化版数据管理器
    class DataManager:
        def __init__(self, data_dir='data'):
            self.data_dir = data_dir
            self.jobs_file = os.path.join(data_dir, 'all_jobs.json')


            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
                
            if not os.path.exists(self.jobs_file):
                with open(self.jobs_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
        
        def save_jobs(self, jobs):
            existing_jobs = self.load_jobs()
            all_jobs = existing_jobs + jobs
            
            with open(self.jobs_file, 'w', encoding='utf-8') as f:
                json.dump(all_jobs, f, ensure_ascii=False, indent=4)
                
            print(f"已将 {len(jobs)} 条新职位数据添加到数据库，总计 {len(all_jobs)} 条")
            return len(all_jobs)
        
        def load_jobs(self):
            try:
                with open(self.jobs_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载数据时出错: {str(e)}")
                return []
        
        def get_stats(self):
            jobs = self.load_jobs()
            stats = {
                "total_records": len(jobs),
                "last_update": max([job.get('crawl_time', '') for job in jobs]) if jobs else 'N/A',
                "earliest_record": min([job.get('crawl_time', '') for job in jobs]) if jobs else 'N/A'
            }
            return stats

class ZhipinSeleniumScraper:
    """
    基于Selenium的Boss直聘数据抓取器
    """
    
    def __init__(self, city="北京", keyword="数据分析", pages=3, timeout=10, debug=True):
        """初始化参数"""
        self.city = city
        self.keyword = keyword
        self.pages = pages
        self.timeout = timeout
        self.debug = debug
        self.debug_dir = "debug"
        self.data_dir = "data"
        
        # 创建debug和data目录
        for directory in [self.debug_dir, self.data_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # 设置日志
        self.setup_logging()
        
        # 初始化浏览器
        self.driver = self.init_driver()
        
        # 数据管理器
        self.data_manager = DataManager(self.data_dir)
        
    def setup_logging(self):
        """设置日志"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(level=logging.INFO, format=log_format)
        self.logger = logging.getLogger(__name__)
        
        if self.debug:
            # 添加文件处理器
            log_file = os.path.join(self.debug_dir, f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(log_format))
            self.logger.addHandler(file_handler)
    
    def init_driver(self):
        """初始化WebDriver，使用多种策略确保稳定性"""
        print("正在初始化Edge浏览器...")
        
        # 配置Edge选项
        options = Options()
        
        # 无头模式（取消注释以启用）
        # options.add_argument('--headless')
        
        # 反爬虫设置
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 随机User-Agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36',
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        # 其他优化选项
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-infobars')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # 尝试多种初始化方式
        driver = None
        error_messages = []
        
        # 定义默认EdgeDriver路径
        default_driver_path = "D:\\BigData\\drivers\\msedgedriver.exe"
        
        # 方法0: 优先使用已知的EdgeDriver路径
        if os.path.exists(default_driver_path):
            try:
                print(f"使用默认EdgeDriver路径: {default_driver_path}")
                service = Service(default_driver_path)
                driver = webdriver.Edge(service=service, options=options)
                print(f"成功初始化Edge浏览器")
                return driver
            except Exception as e:
                error_messages.append(f"默认路径失败: {str(e)}")
                print(f"使用默认EdgeDriver路径初始化失败: {str(e)}")
        
        # 方法1: 仅当默认路径不可用时才询问用户
        if driver is None:
            print("默认EdgeDriver路径无效或无法使用")
            print("请确保安装了Microsoft Edge浏览器")
            print("请前往 https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/ 下载与您Edge版本匹配的WebDriver")
            msedgedriver_path = input("请输入msedgedriver.exe的完整路径（例如：D:\\msedgedriver.exe），或按Enter尝试自动查找: ")
            if msedgedriver_path and os.path.exists(msedgedriver_path):
                try:
                    service = Service(msedgedriver_path)
                    driver = webdriver.Edge(service=service, options=options)
                    print(f"使用用户提供的EdgeDriver路径成功初始化浏览器: {msedgedriver_path}")
                    return driver
                except Exception as e:
                    error_messages.append(f"用户提供的路径失败: {str(e)}")
                    print(f"使用用户提供的EdgeDriver路径初始化失败: {str(e)}")
        
        # 方法2: 使用webdriver_manager自动下载并配置EdgeDriver
        if USE_WEBDRIVER_MANAGER:
            try:
                from webdriver_manager.microsoft import EdgeChromiumDriverManager
                service = Service(EdgeChromiumDriverManager().install())
                driver = webdriver.Edge(service=service, options=options)
                print("使用webdriver_manager成功初始化Edge浏览器")
                return driver
            except Exception as e:
                error_messages.append(f"方法2失败: {str(e)}")
                print(f"使用webdriver_manager初始化失败: {str(e)}")
        
        # 方法3: 使用系统环境中的EdgeDriver
        if driver is None:
            try:
                driver = webdriver.Edge(options=options)
                print("使用系统EdgeDriver成功初始化浏览器")
                return driver
            except Exception as e:
                error_messages.append(f"方法3失败: {str(e)}")
                print(f"使用系统EdgeDriver初始化失败: {str(e)}")
        
        # 方法4: 尝试指定EdgeDriver路径
        if driver is None:
            possible_paths = [
                "./msedgedriver.exe",
                "./drivers/msedgedriver.exe",
                "C:/msedgedriver.exe",
                "D:/msedgedriver.exe",
                "D:/BigData/msedgedriver.exe",
                "D:/BigData/drivers/msedgedriver.exe",
                os.path.join(os.getcwd(), "msedgedriver.exe"),
                os.path.join(os.getcwd(), "drivers", "msedgedriver.exe")
            ]
            
            for driver_path in possible_paths:
                if os.path.exists(driver_path):
                    try:
                        service = Service(driver_path)
                        driver = webdriver.Edge(service=service, options=options)
                        print(f"使用本地EdgeDriver成功初始化浏览器: {driver_path}")
                        return driver
                    except Exception as e:
                        error_messages.append(f"方法4 ({driver_path}) 失败: {str(e)}")
                        print(f"使用本地EdgeDriver ({driver_path}) 初始化失败: {str(e)}")
        
        # 如果所有方法都失败
        if driver is None:
            error_log = os.path.join(self.debug_dir, "webdriver_errors.log")
            with open(error_log, "w", encoding="utf-8") as f:
                f.write("\n\n".join(error_messages))
            
            print(f"所有初始化方法均失败，详细错误信息已保存至 {error_log}")
            print("请手动下载EdgeDriver:")
            print("1. 确认您的Edge浏览器版本: 打开Edge浏览器 -> 右上角三点 -> 设置 -> 关于Microsoft Edge")
            print("2. 前往 https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/ 下载对应版本")
            print("3. 解压并将msedgedriver.exe放到项目根目录或 D:/BigData/drivers/ 目录下")
            raise Exception("初始化WebDriver失败")
        
        # 如果成功初始化，修改navigator.webdriver属性隐藏自动化特征
        try:
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except:
            print("警告: 无法修改navigator.webdriver属性")
        
        return driver
        
    def get_search_url(self, page=1):
        """构建搜索URL"""
        # 优先使用当前浏览器URL，保留所有搜索条件
        if hasattr(self, "current_search_url"):
            # 将页码参数添加到已有URL
            base_url = self.current_search_url
            if "page=" in base_url:
                # 替换现有页码
                return re.sub(r"page=\d+", f"page={page}", base_url)
            elif "?" in base_url:
                # 添加页码参数
                return f"{base_url}&page={page}"
            else:
                # 添加第一个参数
                return f"{base_url}?page={page}"
        
        # 如果没有现有URL，则构建基本URL
        encoded_keyword = quote(self.keyword)
        encoded_city = quote(self.city)
        return f"https://www.zhipin.com/web/geek/job?query={encoded_keyword}&city={encoded_city}&page={page}"
    
    def wait_for_element(self, by, value, timeout=None):
        """等待元素加载"""
        if timeout is None:
            timeout = self.timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.logger.warning(f"等待元素超时: {value}")
            return None
    
    def wait_for_elements(self, by, value, timeout=None):
        """等待多个元素加载"""
        if timeout is None:
            timeout = self.timeout
        try:
            elements = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((by, value))
            )
            return elements
        except TimeoutException:
            self.logger.warning(f"等待元素超时: {value}")
            return []
    
    def save_debug_info(self, page_num):
        """保存调试信息"""
        if self.debug:
            screenshot_path = os.path.join(self.debug_dir, f"page_{page_num}.png")
            source_path = os.path.join(self.debug_dir, f"page_{page_num}.html")
            
            try:
                self.driver.save_screenshot(screenshot_path)
                with open(source_path, "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                self.logger.info(f"保存调试信息: {screenshot_path} 和 {source_path}")
            except Exception as e:
                self.logger.error(f"保存调试信息失败: {str(e)}")
    
    def extract_job_details(self, job_card):
        """提取职位详情"""
        try:
            # 调试：保存一个职位卡片的HTML结构，辅助分析
            try:
                # 确保职位卡片内容完全加载
                WebDriverWait(self.driver, 2).until(
                    lambda x: job_card.get_attribute('outerHTML') and len(job_card.get_attribute('outerHTML')) > 100
                )
                
                card_html = job_card.get_attribute('outerHTML')
                if len(card_html) < 100:  # 检查HTML内容是否太短（可能未加载完成）
                    self.logger.warning(f"职位卡片HTML内容过短，可能未完全加载: {len(card_html)} 字符")
                    # 尝试滚动到这个元素以触发加载
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", job_card)
                    time.sleep(1)  # 等待加载
                    card_html = job_card.get_attribute('outerHTML')
                
                debug_file = os.path.join(self.debug_dir, f"job_card_{datetime.now().strftime('%H%M%S')}.html")
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(card_html)
                self.logger.info(f"已保存职位卡片HTML到: {debug_file} 长度: {len(card_html)} 字符")
                
                # 如果HTML内容仍然太短，尝试获取父元素
                if len(card_html) < 200:
                    try:
                        parent = job_card.find_element(By.XPATH, "./..")
                        parent_html = parent.get_attribute('outerHTML')
                        with open(debug_file + ".parent.html", "w", encoding="utf-8") as f:
                            f.write(parent_html)
                        self.logger.info(f"已保存父元素HTML到: {debug_file}.parent.html 长度: {len(parent_html)} 字符")
                        
                        # 如果父元素内容更丰富，使用父元素代替
                        if len(parent_html) > len(card_html) * 2:
                            job_card = parent
                            card_html = parent_html
                            self.logger.info("使用父元素替代原始职位卡片")
                    except:
                        self.logger.warning("尝试获取父元素失败")
            except Exception as e:
                self.logger.warning(f"无法保存职位卡片HTML: {str(e)}")
            
            # 直接使用XPath选择器可能更准确
            xpath_selectors = {
                "job_name": [
                    ".//span[@class='job-name']", 
                    ".//a[contains(@class, 'job-name')]",
                    ".//span[contains(@class, 'job-title')]",
                    ".//div[contains(@class, 'job-title')]",
                    ".//div[contains(@class, 'name')]//span",
                    ".//p[contains(@class, 'name')]"
                ],
                "salary": [
                    ".//span[@class='salary']", 
                    ".//span[contains(@class, 'red')]",
                    ".//span[contains(@class, 'price')]",
                    ".//span[contains(@class, 'money')]",
                    ".//p[contains(@class, 'salary')]"
                ],
                "company_name": [
                    ".//div[@class='company-name']", 
                    ".//a[contains(@class, 'company-name')]",
                    ".//span[contains(@class, 'company')]",
                    ".//h3[contains(@class, 'company')]",
                    ".//h3[contains(@class, 'company-name')]//a"
                ],
                "job_area": [
                    ".//span[@class='job-area']", 
                    ".//span[contains(@class, 'address')]",
                    ".//span[contains(@class, 'area')]",
                    ".//span[contains(@class, 'location')]",
                    ".//p[contains(@class, 'job-text')]//span[1]",
                    ".//span[contains(@class, 'job-area-wrapper')]//span"
                ]
            }
            
            # 尝试多种选择器组合 - CSS选择器
            css_selectors = {
                "job_name": [".job-name", ".job-title", "a.job-name", "a[ka=job-title]", ".name span", "p.name"],
                "salary": [".salary", ".red", ".job-limit-tip", ".price", ".money", "p.salary"],
                "company_name": [".company-name", ".company-text", "a[ka=job-company]", ".company", "h3.company-name a"],
                "job_area": [".job-area", ".job-address", ".location-name", ".address", ".area", "p.job-text span:first-child", ".job-area-wrapper span"]
            }
            
            job_data = {
                "job_name": "未知",
                "salary": "未知",
                "company_name": "未知",
                "job_area": "未知",
                "job_requirements": [],
                "hr_name": "未知",
                "hr_title": "未知",
                "publish_time": "未知",
                "detail_link": "",
                "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 首先尝试XPath选择器
            for field, xpath_list in xpath_selectors.items():
                for xpath in xpath_list:
                    try:
                        elements = job_card.find_elements(By.XPATH, xpath)
                        if elements and elements[0].text.strip():
                            job_data[field] = elements[0].text.strip()
                            self.logger.info(f"使用XPath '{xpath}' 成功提取 {field}: {job_data[field]}")
                            break
                    except Exception as e:
                        continue
            
            # 如果XPath没有找到，再尝试CSS选择器
            for field, selector_list in css_selectors.items():
                if job_data[field] == "未知":  # 只有在XPath未找到时才尝试
                    for selector in selector_list:
                        try:
                            elements = job_card.find_elements(By.CSS_SELECTOR, selector)
                            if elements and elements[0].text.strip():
                                job_data[field] = elements[0].text.strip()
                                self.logger.info(f"使用CSS '{selector}' 成功提取 {field}: {job_data[field]}")
                                break
                        except:
                            continue
            
            # 提取职位要求 - 更多的选择器
            requirement_xpaths = [
                ".//div[contains(@class, 'tags')]//span",
                ".//div[contains(@class, 'job-info-tags')]//span",
                ".//div[contains(@class, 'tag')]//span",
                ".//div[contains(@class, 'requirement')]//span",
                ".//ul[contains(@class, 'tag-list')]//li",
                ".//div[contains(@class, 'job-card-footer')]//ul[contains(@class, 'tag-list')]//li"
            ]
            
            for xpath in requirement_xpaths:
                try:
                    elements = job_card.find_elements(By.XPATH, xpath)
                    if elements:
                        job_data["job_requirements"] = [e.text.strip() for e in elements if e.text.strip()]
                        if job_data["job_requirements"]:
                            self.logger.info(f"使用XPath '{xpath}' 成功提取职位要求: {job_data['job_requirements']}")
                            break
                except:
                    continue
            
            if not job_data["job_requirements"]:  # 如果XPath未提取到，尝试CSS选择器
                requirements_selectors = [
                    ".job-info-tags .tag-item", ".tags span", ".tag",
                    ".requirement", ".text-ellipsis", "ul.tag-list li",
                    ".job-card-footer ul.tag-list li"
                ]
                for selector in requirements_selectors:
                    try:
                        elements = job_card.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            job_data["job_requirements"] = [e.text.strip() for e in elements if e.text.strip()]
                            if job_data["job_requirements"]:
                                self.logger.info(f"使用CSS '{selector}' 成功提取职位要求")
                                break
                    except:
                        continue
            
            # 提取HR信息 - 更多尝试
            hr_xpaths = [
                ".//div[contains(@class, 'info-public')]",
                ".//div[contains(@class, 'boss-info')]",
                ".//div[contains(@class, 'job-author')]",
                ".//div[contains(@class, 'hr')]",
                ".//div[contains(@class, 'publisher')]"
            ]
            
            for xpath in hr_xpaths:
                try:
                    elements = job_card.find_elements(By.XPATH, xpath)
                    if elements and elements[0].text.strip():
                        hr_info = elements[0].text.strip()
                        hr_parts = hr_info.split("·") if "·" in hr_info else hr_info.split(" ")
                        if len(hr_parts) >= 1:
                            job_data["hr_name"] = hr_parts[0].strip()
                        if len(hr_parts) >= 2:
                            job_data["hr_title"] = hr_parts[1].strip()
                        self.logger.info(f"使用XPath '{xpath}' 成功提取HR信息")
                        break
                except:
                    continue
            
            # 提取发布时间 - 增加尝试
            time_xpaths = [
                ".//span[contains(@class, 'job-info-tip')]",
                ".//span[contains(@class, 'job-time')]",
                ".//span[contains(@class, 'time')]",
                ".//span[contains(@class, 'publish-time')]",
                ".//span[contains(@class, 'update-time')]"
            ]
            
            for xpath in time_xpaths:
                try:
                    elements = job_card.find_elements(By.XPATH, xpath)
                    if elements and elements[0].text.strip():
                        job_data["publish_time"] = elements[0].text.strip()
                        self.logger.info(f"使用XPath '{xpath}' 成功提取发布时间: {job_data['publish_time']}")
                        break
                except:
                    continue
            
            # 提取详情链接 - 尝试查找整个卡片中的链接
            try:
                # 寻找任何链接元素
                links = job_card.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and ("job_detail" in href or "geek/job" in href):
                        job_data["detail_link"] = href
                        self.logger.info(f"成功提取详情链接: {href}")
                        break
            except:
                pass
            
            # 如果仍然找不到详情链接，尝试父元素的链接
            if not job_data["detail_link"]:
                try:
                    parent = job_card.find_element(By.XPATH, "./..")
                    href = parent.get_attribute("href")
                    if href:
                        job_data["detail_link"] = href
                        self.logger.info(f"从父元素提取详情链接: {href}")
                except:
                    pass
            
            # 检查是否提取到了有效信息
            valid_fields = 0
            for key, value in job_data.items():
                if key != "crawl_time" and key != "job_requirements" and value != "未知":
                    valid_fields += 1
            
            # 更宽松的标准：即使只有一个有效字段也接受（增加成功率）
            if valid_fields < 1:
                self.logger.warning(f"未能提取足够的职位信息: {job_data}")
                # 最后尝试：导出职位卡片的完整HTML并检查关键字
                card_html = job_card.get_attribute('outerHTML')
                if '立即沟通' in card_html and len(card_html) < 200:
                    self.logger.warning("检测到只有'立即沟通'按钮，职位卡片可能未完全加载")
                    return None
                
                # 尝试在HTML中查找关键信息
                import re
                salary_match = re.search(r'(\d+)[K-](\d+)K', card_html)
                if salary_match:
                    job_data["salary"] = f"{salary_match.group(1)}-{salary_match.group(2)}K"
                    valid_fields += 1
                
                job_title_match = re.search(r'job-name"[^>]*>([^<]+)<', card_html)
                if job_title_match:
                    job_data["job_name"] = job_title_match.group(1)
                    valid_fields += 1
                
                if valid_fields < 1:
                    return None
                
            return job_data
        
        except Exception as e:
            self.logger.error(f"提取职位详情失败: {str(e)}")
            traceback.print_exc()
            return None
    
    def scrape_page(self, page_num):
        """抓取一页数据"""
        url = self.get_search_url(page_num)
        self.logger.info(f"开始抓取第{page_num}页: {url}")
        
        try:
            self.driver.get(url)
            
            # 增加页面加载等待时间
            self.logger.info("等待页面加载...")
            time.sleep(5)  # 增加到5秒
            
            # 保存当前页面状态以便调试
            self.save_debug_info(page_num)
            
            # 尝试检测页面状态
            page_title = self.driver.title
            self.logger.info(f"页面标题: {page_title}")
            
            # 检查是否显示"没有找到相关职位"
            no_job_indicators = [
                "没有找到相关职位",
                "打开APP查看全部职位库",
                "优质职位随心刷"
            ]
            
            page_text = self.driver.page_source
            for indicator in no_job_indicators:
                if indicator in page_text:
                    self.logger.warning(f"检测到无搜索结果提示: '{indicator}'")
                    print(f"\n当前搜索条件 '{self.keyword}' 在 '{self.city}' 没有找到职位")
                    
                    # 提示用户是否要更改搜索条件
                    change = input("是否要更改搜索条件？(y/n): ")
                    if change.lower() == 'y':
                        # 获取新的搜索条件
                        new_keyword = input(f"请输入新的关键词(当前: {self.keyword}): ")
                        if new_keyword.strip():
                            self.keyword = new_keyword.strip()
                        
                        new_city = input(f"请输入新的城市(当前: {self.city}): ")
                        if new_city.strip():
                            self.city = new_city.strip()
                        
                        # 使用自动方式设置新的搜索条件
                        if self.select_search_criteria():
                            # 更新当前搜索URL
                            self.current_search_url = self.driver.current_url
                            # 重新抓取
                            return self.scrape_page(page_num)
                    return []
            
            # 尝试多个可能的CSS选择器查找职位列表
            selectors = [
                ".job-list-box",           # 原始选择器
                ".job-list",               # 可能的替代选择器
                ".search-job-result",      # 另一个可能的选择器
                ".job-card-wrapper",       # 直接查找职位卡片
                ".job-primary",            # 另一种职位卡片包装
                ".search-job-result ul li", # 列表项
                ".job-card"                # 可能的卡片选择器
            ]
            
            job_list = None
            found_selector = None
            
            for selector in selectors:
                try:
                    self.logger.info(f"尝试查找选择器: {selector}")
                    elements = self.wait_for_elements(By.CSS_SELECTOR, selector, timeout=3)
                    if elements and len(elements) > 0:
                        job_list = elements
                        found_selector = selector
                        self.logger.info(f"成功找到选择器 {selector}，元素数量: {len(elements)}")
                        break
                except Exception as e:
                    self.logger.warning(f"选择器 {selector} 查找失败: {str(e)}")
            
            if not job_list:
                self.logger.warning(f"第{page_num}页没有找到职位列表")
                
                # 使用自动设置搜索条件重试
                print("\n找不到职位列表，尝试重新设置搜索条件...")
                if self.select_search_criteria():
                    # 更新当前搜索URL
                    self.current_search_url = self.driver.current_url
                    # 重新尝试抓取当前页面
                    return self.scrape_page(page_num)
                return []
            
            # 如果找到了职位列表但不是职位卡片，需要进一步查找职位卡片
            job_cards = []
            if found_selector != ".job-card-wrapper" and found_selector != ".job-primary" and found_selector != ".job-card":
                # 根据找到的容器再查找职位卡片
                for container in job_list:
                    try:
                        cards = container.find_elements(By.CSS_SELECTOR, ".job-card-wrapper, .job-primary, .job-card, a")
                        if cards:
                            job_cards.extend(cards)
                    except:
                        pass
            else:
                job_cards = job_list
            
            if not job_cards:
                self.logger.warning(f"第{page_num}页没有找到职位卡片")
                return []
            
            self.logger.info(f"第{page_num}页找到{len(job_cards)}个职位")
            
            # 尝试不同方式提取数据
            jobs_data = []
            for job_card in job_cards:
                try:
                    job_data = self.extract_job_details(job_card)
                    if job_data:
                        jobs_data.append(job_data)
                    
                    # 随机休眠，避免被检测
                    time.sleep(random.uniform(0.5, 1.5))
                except Exception as e:
                    self.logger.error(f"处理职位卡片时出错: {str(e)}")
            
            self.logger.info(f"第{page_num}页成功提取{len(jobs_data)}个职位数据")
            
            return jobs_data
            
        except Exception as e:
            self.logger.error(f"抓取第{page_num}页失败: {str(e)}")
            traceback.print_exc()
            self.save_debug_info(page_num)
            return []
    
    def scrape_all(self):
        """抓取所有页面数据"""
        all_jobs = []
        
        for page in range(1, self.pages + 1):
            jobs_data = self.scrape_page(page)
            all_jobs.extend(jobs_data)
            
            # 保存中间结果
            self.save_results(all_jobs, f"zhipin_{self.city}_{self.keyword}_page_{page}.json")
            
            # 随机休眠，避免被检测
            if page < self.pages:
                sleep_time = random.uniform(2, 5)
                self.logger.info(f"休眠{sleep_time:.2f}秒后继续下一页")
                time.sleep(sleep_time)
        
        return all_jobs
    
    def save_results(self, data, filename=None):
        """保存结果"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"zhipin_{self.city}_{self.keyword}_{timestamp}.json"
        
        # 确保文件保存在data目录中
        if not filename.startswith(self.data_dir):
            filename = os.path.join(self.data_dir, filename)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"成功保存{len(data)}条数据到{filename}")
            
            # 同时保存到数据管理器
            self.data_manager.save_jobs(data)
        except Exception as e:
            self.logger.error(f"保存数据失败: {str(e)}")
    
    def login(self):
        """让用户登录BOSS直聘"""
        self.logger.info("正在打开BOSS直聘首页，等待用户登录...")
        print("\n正在打开BOSS直聘首页...")
        
        try:
            # 访问主页
            self.driver.get("https://www.zhipin.com/")
            time.sleep(2)
            
            # 提示用户登录
            print("\n请在浏览器中完成登录操作:")
            print("1. 可以使用微信扫码或手机验证码登录")
            print("2. 如遇到验证码，请手动完成验证")
            print("3. 确保完全登录成功后再继续")
            
            login_input = input("\n完成登录后按Enter继续，或输入'q'退出: ")
            if login_input.lower() == 'q':
                print("用户取消爬取，正在退出...")
                self.close()
                return False
                
            # 验证是否登录成功
            try:
                # 可以检查是否有用户头像或个人信息元素来判断登录状态
                self.wait_for_element(By.CSS_SELECTOR, ".user-nav", timeout=5)
                print("登录成功！")
                self.logger.info("用户已成功登录")
                return True
            except:
                print("似乎未登录成功，但将继续尝试爬取...")
                self.logger.warning("可能未登录成功")
                return True  # 仍然继续，让用户决定
        
        except Exception as e:
            self.logger.error(f"登录过程出错: {str(e)}")
            print(f"登录过程出错: {str(e)}")
            return False
            
    def select_search_criteria(self):
        """自动设置搜索条件（城市和关键词）"""
        self.logger.info("正在设置搜索条件...")
        print(f"\n正在自动设置搜索条件：城市[{self.city}]，关键词[{self.keyword}]")
        
        try:
            # 访问搜索页面 - 直接使用首页，因为它有搜索框
            self.driver.get("https://www.zhipin.com/")
            time.sleep(3)
            
            # 保存当前页面源码到调试文件
            debug_file = os.path.join(self.debug_dir, "page_before_search.html")
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            self.logger.info(f"已保存页面源码到: {debug_file}")
            
            # 保存屏幕截图
            screenshot_file = os.path.join(self.debug_dir, "screenshot_before_search.png")
            self.driver.save_screenshot(screenshot_file)
            self.logger.info(f"已保存屏幕截图到: {screenshot_file}")
            
            # 城市映射表：城市名称到城市代码的映射
            city_codes = {
                "北京": "101010100",
                "上海": "101020100",
                "广州": "101280100",
                "深圳": "101280600",
                "杭州": "101210100",
                "苏州": "101190400",
                "南京": "101190100",
                "天津": "101030100",
                "成都": "101270100",
                "武汉": "101200100",
                "西安": "101110100",
                "重庆": "101040100",
                "郑州": "101180100",
                "长沙": "101250100",
                "大连": "101070200",
                "青岛": "101120200",
                "宁波": "101210400",
                "厦门": "101230200",
                "福州": "101230100",
                "济南": "101120100",
                "合肥": "101220100",
                "石家庄": "101090100",
                "哈尔滨": "101050100",
                "全国": "100010000"
            }
            
            # 获取当前城市
            current_city = None
            try:
                city_elements = self.driver.find_elements(By.CSS_SELECTOR, ".city-cur")
                if city_elements and len(city_elements) > 0:
                    current_city = city_elements[0].text.strip()
                    self.logger.info(f"当前城市: {current_city}")
            except Exception as e:
                self.logger.warning(f"无法获取当前城市: {str(e)}")
            
            # 检查是否需要更改城市
            need_change_city = True
            if current_city and current_city == self.city:
                need_change_city = False
                self.logger.info(f"当前城市已经是 {self.city}，无需更改")
            
            # 如果需要更改城市，尝试点击切换城市
            if need_change_city:
                try:
                    # 尝试点击城市选择按钮
                    city_selectors = [".city-cur", ".city-select", ".dropdown-select"]
                    
                    for selector in city_selectors:
                        try:
                            city_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if city_element:
                                city_element.click()
                                self.logger.info(f"点击了城市选择按钮: {selector}")
                                time.sleep(2) # 等待城市选择弹窗出现
                                
                                # 尝试在弹出的城市列表中选择目标城市
                                city_options = self.driver.find_elements(By.CSS_SELECTOR, ".city-list a")
                                for option in city_options:
                                    if option.text.strip() == self.city:
                                        option.click()
                                        self.logger.info(f"成功选择城市: {self.city}")
                                        time.sleep(2) # 等待页面更新
                                        break
                                break
                        except:
                            continue
                except Exception as e:
                    self.logger.warning(f"尝试切换城市失败: {str(e)}")
            
            # 设置搜索关键词
            search_input = None
            search_selectors = [
                ".search-form input[name='query']",
                ".search-box input[type='text']",
                ".search-box input",
                ".ipt-search",
                "input[placeholder*='搜索']",
                "input.ipt"
            ]
            
            for selector in search_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and len(elements) > 0:
                        search_input = elements[0]
                        self.logger.info(f"找到搜索输入框: {selector}")
                        break
                except:
                    continue
            
            if search_input:
                # 清除现有内容
                search_input.clear()
                # 输入搜索关键词
                search_input.send_keys(self.keyword)
                self.logger.info(f"已输入搜索关键词: {self.keyword}")
            else:
                self.logger.warning("未找到搜索输入框")
                print(f"注意: 无法自动设置搜索关键词")
                return self.manual_select_search_criteria()
            
            # 点击搜索按钮
            search_button = None
            button_selectors = [
                ".search-form .btn-search",
                ".btn-search",
                ".search-box button",
                "button[type='submit']",
                ".search-box .btn"
            ]
            
            for selector in button_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and len(elements) > 0:
                        search_button = elements[0]
                        self.logger.info(f"找到搜索按钮: {selector}")
                        break
                except:
                    continue
            
            if search_button:
                search_button.click()
                self.logger.info("已点击搜索按钮")
            else:
                # 尝试键盘按回车键
                if search_input:
                    try:
                        search_input.send_keys(Keys.ENTER)
                        self.logger.info("已通过回车键触发搜索")
                    except:
                        self.logger.error("无法通过回车键触发搜索")
                        print("注意: 无法触发搜索，请检查页面状态")
                        return self.manual_select_search_criteria()
            
            # 等待页面加载
            time.sleep(5)
            
            # 获取当前URL并修改城市代码（如果需要）
            current_url = self.driver.current_url
            self.logger.info(f"搜索后URL: {current_url}")
            
            # 关键步骤：如果需要更改城市，直接修改URL
            if need_change_city and self.city in city_codes:
                city_code = city_codes[self.city]
                new_url = ""
                
                if "city=" in current_url:
                    # 替换现有城市代码
                    new_url = re.sub(r"city=\d+", f"city={city_code}", current_url)
                elif "?" in current_url:
                    # 添加城市参数
                    new_url = f"{current_url}&city={city_code}"
                else:
                    # 添加第一个参数
                    new_url = f"{current_url}?city={city_code}"
                
                self.logger.info(f"修改URL中的城市参数: {new_url}")
                self.driver.get(new_url)
                time.sleep(3)
                
                # 确认URL已更改
                current_url = self.driver.current_url
                if f"city={city_code}" in current_url:
                    self.logger.info(f"成功更改城市代码为: {city_code} ({self.city})")
                    print(f"已切换到城市: {self.city}")
                else:
                    self.logger.warning(f"可能未成功切换城市，当前URL: {current_url}")
                    print(f"警告: 可能未成功切换到城市 {self.city}，请检查搜索结果")
            
            # 保存最终URL
            self.current_search_url = current_url
            self.logger.info(f"最终搜索URL: {current_url}")
            
            # 验证当前页面的城市设置是否正确
            try:
                # 尝试从页面元素中获取当前城市
                city_elements = self.driver.find_elements(By.CSS_SELECTOR, ".city-cur, .selected-text")
                if city_elements and len(city_elements) > 0:
                    detected_city = city_elements[0].text.strip()
                    if detected_city != self.city:
                        self.logger.warning(f"页面显示的城市是 {detected_city}，而不是期望的 {self.city}")
                        print(f"警告: 页面显示的城市是 {detected_city}，而不是 {self.city}")
                        
                        # 最后尝试手动设置城市
                        if input(f"是否要手动设置城市? (y/n): ").lower() == 'y':
                            return self.manual_select_search_criteria()
            except Exception as e:
                self.logger.warning(f"验证城市设置时出错: {str(e)}")
            
            # 保存搜索后的页面状态
            debug_file = os.path.join(self.debug_dir, "page_after_search.html")
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            self.logger.info(f"已保存搜索后页面源码到: {debug_file}")
            
            # 保存搜索后的屏幕截图
            screenshot_file = os.path.join(self.debug_dir, "screenshot_after_search.png")
            self.driver.save_screenshot(screenshot_file)
            self.logger.info(f"已保存搜索后屏幕截图到: {screenshot_file}")
            
            print(f"\n成功设置搜索条件: 城市 '{self.city}'，关键词 '{self.keyword}'")
            print(f"搜索URL: {current_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置搜索条件过程出错: {str(e)}")
            print(f"设置搜索条件过程出错: {str(e)}")
            traceback.print_exc()
            
            # 如果自动设置失败，提供手动设置选项
            manual_option = input("自动设置失败，是否要手动设置搜索条件？(y/n): ")
            if manual_option.lower() == 'y':
                return self.manual_select_search_criteria()
            return False
            
    def manual_select_search_criteria(self):
        """手动设置搜索条件（城市和关键词）"""
        self.logger.info("正在手动设置搜索条件...")
        print("\n现在请设置搜索条件（城市和关键词）")
        
        try:
            # 重新加载搜索页面
            self.driver.get("https://www.zhipin.com/web/geek/job")
            time.sleep(3)
            
            # 指导用户进行手动设置
            print("\n请在浏览器中手动设置搜索条件:")
            print("1. 点击左上角城市下拉框，选择您想要搜索的城市")
            print("2. 在搜索框中输入您想要的关键词")
            print("3. 可以设置其他筛选条件（公司规模、薪资范围等）")
            print("4. 完成设置后，点击'搜索'按钮")
            
            # 等待用户操作
            input("\n完成搜索条件设置并点击搜索后，按Enter继续: ")
            
            # 等待页面加载
            time.sleep(3)
            
            # 获取当前URL
            current_url = self.driver.current_url
            self.logger.info(f"当前搜索URL: {current_url}")
            
            # 尝试从页面中获取实际选择的城市和关键词
            try:
                # 尝试获取城市名称
                city_element = self.driver.find_element(By.CSS_SELECTOR, ".city-select .dropdown-select")
                if city_element:
                    self.city = city_element.text.strip()
                    
                # 尝试获取关键词
                keyword_element = self.driver.find_element(By.CSS_SELECTOR, ".search-form input[name='query']")
                if keyword_element:
                    self.keyword = keyword_element.get_attribute("value")
                    
                print(f"\n当前搜索条件: 城市 '{self.city}'，关键词 '{self.keyword}'")
            except Exception as e:
                self.logger.warning(f"无法获取搜索条件: {str(e)}")
                # 如果无法获取，可以让用户手动输入
                city_input = input("请确认城市名称: ")
                keyword_input = input("请确认搜索关键词: ")
                
                if city_input.strip():
                    self.city = city_input.strip()
                if keyword_input.strip():
                    self.keyword = keyword_input.strip()
            
            return True
            
        except Exception as e:
            self.logger.error(f"手动设置搜索条件过程出错: {str(e)}")
            print(f"手动设置搜索条件过程出错: {str(e)}")
            return False
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            self.logger.info("浏览器已关闭")

    def scrape_job_list(self):
        """抓取职位列表，更稳定的处理方式"""
        self.logger.info(f"开始抓取职位列表：城市[{self.city}]，关键词[{self.keyword}]")
        all_jobs = []
        
        try:
            # 首先确保我们在搜索结果页面
            if not self.current_search_url or "zhipin.com" not in self.driver.current_url:
                self.logger.info("未检测到搜索URL，重新设置搜索条件")
                if not self.select_search_criteria():
                    raise Exception("无法设置搜索条件")
                self.current_search_url = self.driver.current_url
            
            # 确保页面完全加载
            try:
                # 等待搜索框加载完成
                search_box = WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".search-form, .search-box, input[name='query']"))
                )
                self.logger.info("搜索框已加载")
                
                # 等待职位列表容器加载
                job_list_container = WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".job-list-box, .job-list, .search-job-result"))
                )
                self.logger.info("职位列表容器已加载")
            except TimeoutException:
                self.logger.warning("等待页面元素超时，将保存页面源码进行调试")
                debug_file = os.path.join(self.debug_dir, f"timeout_page_{datetime.now().strftime('%H%M%S')}.html")
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                self.logger.info(f"已保存页面源码到: {debug_file}")
                
                # 尝试强制刷新页面
                self.driver.refresh()
                time.sleep(5)
            
            # 开始逐页爬取数据
            for page in range(1, self.pages + 1):
                page_url = self.get_search_url(page)
                self.logger.info(f"开始爬取第{page}页: {page_url}")
                
                try:
                    # 访问页面
                    self.driver.get(page_url)
                    
                    # 等待页面加载
                    time.sleep(5)
                    
                    # 保存页面状态以便调试
                    self.save_debug_info(page)
                    
                    # 尝试多种选择器找到职位卡片
                    job_cards = []
                    selectors = [
                        ".job-card-wrapper",
                        ".job-primary",
                        ".job-card",
                        ".search-job-result ul li",
                        ".job-list-box li"
                    ]
                    
                    for selector in selectors:
                        try:
                            self.logger.info(f"尝试选择器: {selector}")
                            elements = self.wait_for_elements(By.CSS_SELECTOR, selector, timeout=3)
                            if elements and len(elements) > 0:
                                job_cards = elements
                                self.logger.info(f"使用选择器 {selector} 找到 {len(elements)} 个职位卡片")
                                break
                        except Exception as e:
                            self.logger.warning(f"选择器 {selector} 失败: {str(e)}")
                    
                    # 如果CSS选择器都失败了，尝试XPath
                    if not job_cards:
                        xpath_selectors = [
                            "//div[contains(@class, 'job-card')]",
                            "//li[contains(@class, 'job-card')]",
                            "//div[contains(@class, 'job-list-box')]//li",
                            "//div[contains(@class, 'search-job-result')]//li"
                        ]
                        
                        for xpath in xpath_selectors:
                            try:
                                elements = self.driver.find_elements(By.XPATH, xpath)
                                if elements and len(elements) > 0:
                                    job_cards = elements
                                    self.logger.info(f"使用XPath {xpath} 找到 {len(elements)} 个职位卡片")
                                    break
                            except:
                                pass
                    
                    # 如果仍然没有找到卡片，保存页面并跳到下一页
                    if not job_cards:
                        self.logger.warning(f"第{page}页未找到职位卡片")
                        
                        # 保存页面源码
                        debug_file = os.path.join(self.debug_dir, f"no_jobs_page_{page}_{datetime.now().strftime('%H%M%S')}.html")
                        with open(debug_file, "w", encoding="utf-8") as f:
                            f.write(self.driver.page_source)
                        self.logger.info(f"已保存无职位卡片页面到: {debug_file}")
                        
                        continue
                    
                    # 确保所有卡片加载完全 - 滚动页面
                    self.logger.info("滚动页面以加载所有职位卡片")
                    for _ in range(3):  # 滚动3次确保加载
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                    
                    # 重新获取职位卡片（滚动后可能有更多卡片加载出来）
                    if len(job_cards) < 10:  # 如果卡片数量太少，尝试重新获取
                        for selector in selectors:
                            try:
                                elements = self.wait_for_elements(By.CSS_SELECTOR, selector, timeout=2)
                                if elements and len(elements) > len(job_cards):
                                    job_cards = elements
                                    self.logger.info(f"滚动后重新获取，找到 {len(elements)} 个职位卡片")
                                    break
                            except:
                                pass
                    
                    # 提取每个职位的数据
                    page_jobs = []
                    for job_card in job_cards:
                        try:
                            job_data = self.extract_job_details(job_card)
                            if job_data:
                                page_jobs.append(job_data)
                            
                            # 随机休眠，避免被检测
                            time.sleep(random.uniform(0.3, 0.8))
                        except Exception as e:
                            self.logger.error(f"处理职位卡片失败: {str(e)}")
                    
                    # 记录本页提取的职位数量
                    self.logger.info(f"第{page}页成功提取 {len(page_jobs)}/{len(job_cards)} 个职位数据")
                    
                    # 将本页数据添加到总结果中
                    all_jobs.extend(page_jobs)
                    
                    # 保存每页的临时结果
                    temp_filename = f"zhipin_{self.city}_{self.keyword}_page_{page}_temp.json"
                    self.save_results(page_jobs, temp_filename)
                    
                    # 随机休眠，避免被检测
                    if page < self.pages:
                        sleep_time = random.uniform(2, 4)
                        self.logger.info(f"休眠 {sleep_time:.2f} 秒后继续下一页")
                        time.sleep(sleep_time)
                    
                except Exception as e:
                    self.logger.error(f"爬取第{page}页时出错: {str(e)}")
                    traceback.print_exc()
            
            # 保存最终结果
            if all_jobs:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                final_filename = f"zhipin_{self.city}_{self.keyword}_{timestamp}_final.json"
                self.save_results(all_jobs, final_filename)
                self.logger.info(f"已将所有 {len(all_jobs)} 条职位数据保存到 {final_filename}")
            else:
                self.logger.warning("未获取到任何职位数据")
            
            return all_jobs
            
        except Exception as e:
            self.logger.error(f"职位列表抓取失败: {str(e)}")
            traceback.print_exc()
            return []

def main():
    # 提示用户输入参数
    print("===== BOSS直聘职位数据爬虫 (Edge版) =====")
    
    city_input = input("请输入要爬取的城市（默认为北京）: ")
    city = city_input.strip() if city_input.strip() else "北京"
    
    keyword_input = input("请输入要搜索的职位关键词（默认为数据分析）: ")
    keyword = keyword_input.strip() if keyword_input.strip() else "数据分析"
    
    pages_input = input("请输入要爬取的页数（默认为3）: ")
    try:
        pages = int(pages_input) if pages_input.strip() else 3
    except ValueError:
        print("输入的页数无效，使用默认值3")
        pages = 3
    
    print(f"\n即将开始爬取...")
    print(f"城市: {city}")
    print(f"关键词: {keyword}")
    print(f"页数: {pages}")
    
    confirm = input("\n确认开始爬取? (y/n): ")
    if confirm.lower() != 'y':
        print("已取消爬取")
        return
    
    # 创建抓取器实例
    scraper = ZhipinSeleniumScraper(city=city, keyword=keyword, pages=pages)
    
    try:
        # 跳过登录，直接设置搜索条件
        print("已跳过登录步骤，直接进行搜索")
        
        # 手动设置搜索条件
        if not scraper.select_search_criteria():
            print("设置搜索条件失败，爬取已取消")
            return
            
        # 存储当前URL用于后续翻页
        scraper.current_search_url = scraper.driver.current_url
            
        # 开始抓取
        all_jobs = scraper.scrape_job_list()
        
        # 保存最终结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"zhipin_{city}_{keyword}_{timestamp}_final.json"
        scraper.save_results(all_jobs, final_filename)
        
        # 打印统计信息
        print(f"\n===== 爬取完成 =====")
        print(f"成功抓取{len(all_jobs)}条职位数据")
        print(f"数据已保存到: {os.path.join('data', final_filename)}")
        
        # 显示数据库统计
        stats = scraper.data_manager.get_stats()
        print(f"\n数据库统计:")
        print(f"总记录数: {stats['total_records']}")
        print(f"最早记录: {stats['earliest_record']}")
        print(f"最近更新: {stats['last_update']}")
        
    except Exception as e:
        print(f"抓取过程发生错误: {str(e)}")
        traceback.print_exc()
    finally:
        # 关闭浏览器
        scraper.close()

if __name__ == "__main__":
    main() 