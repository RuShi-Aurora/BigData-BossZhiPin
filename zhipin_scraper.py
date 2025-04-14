import os
import time
import random
import json
import csv
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from data_manager import DataManager

class ZhipinScraper:
    def __init__(self):
        self.jobs = []
        self.data_dir = 'data'
        self.data_manager = DataManager(self.data_dir)
        
        # 确保数据目录存在
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # 爬虫设置
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.zhipin.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        # 默认使用的搜索关键词
        self.default_keywords = ['Python', '数据分析', '前端', 'Java', '人工智能']
        
    def generate_mock_data(self, count=10):
        """生成模拟数据用于测试 - 保留作为备选方案"""
        job_titles = ["Python开发工程师", "数据分析师", "前端开发工程师", "Java开发工程师", "人工智能工程师"]
        companies = ["腾讯", "阿里巴巴", "百度", "字节跳动", "美团", "京东", "华为", "小米"]
        salaries = ["15K-25K", "20K-40K", "30K-50K", "25K-35K", "18K-30K"]
        locations = ["北京", "上海", "深圳", "广州", "杭州", "成都"]
        experiences = ["1-3年", "3-5年", "5-10年", "不限"]
        
        for _ in range(count):
            job_info = {
                'title': random.choice(job_titles),
                'company': random.choice(companies),
                'salary': random.choice(salaries),
                'location': random.choice(locations),
                'experience': random.choice(experiences),
                'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.jobs.append(job_info)
            
        print(f"成功生成 {count} 条模拟职位数据")
        
    def scrape_zhipin(self, keywords=None, city='101010100', pages=2):
        """
        爬取BOSS直聘网站的职位数据
        :param keywords: 搜索关键词列表，如果为None则使用默认关键词
        :param city: 城市代码，默认为北京(101010100)
        :param pages: 每个关键词爬取的页数
        :return: 爬取的职位数量
        """
        if keywords is None:
            keywords = self.default_keywords
            
        total_scraped = 0
        
        # 城市代码映射
        city_codes = {
            '北京': '101010100',
            '上海': '101020100',
            '广州': '101280100',
            '深圳': '101280600',
            '杭州': '101210100',
            '成都': '101270100'
        }
        
        # 对每个关键词进行爬取
        for keyword in keywords:
            print(f"正在爬取关键词: {keyword}")
            
            for page in range(1, pages + 1):
                try:
                    print(f"  爬取第 {page} 页...")
                    
                    # 构建URL - 这里使用的是BOSS直聘搜索页面的URL格式
                    url = f"https://www.zhipin.com/web/geek/job?query={keyword}&city={city}&page={page}"
                    
                    # 发送请求
                    response = requests.get(url, headers=self.headers)
                    
                    # 如果响应状态码不是200，跳过本次循环
                    if response.status_code != 200:
                        print(f"  请求失败，状态码: {response.status_code}")
                        continue
                    
                    # 解析HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 获取职位列表
                    job_list = soup.select('ul.job-list-box li')
                    
                    if not job_list:
                        print("  未找到职位信息，可能是页面结构变化或IP被封")
                        break
                    
                    # 解析每个职位
                    for job_item in job_list:
                        try:
                            # 提取职位信息
                            title_elem = job_item.select_one('.job-title')
                            company_elem = job_item.select_one('.company-name')
                            salary_elem = job_item.select_one('.salary')
                            location_elem = job_item.select_one('.job-area')
                            experience_elem = job_item.select_one('.job-info .experience')
                            
                            # 跳过没有找到完整信息的职位
                            if not all([title_elem, company_elem, salary_elem, location_elem]):
                                continue
                            
                            # 提取文本并清理
                            title = title_elem.text.strip() if title_elem else "未知职位"
                            company = company_elem.text.strip() if company_elem else "未知公司"
                            salary = salary_elem.text.strip() if salary_elem else "薪资面议"
                            location = location_elem.text.strip() if location_elem else "未知地点"
                            experience = experience_elem.text.strip() if experience_elem else "经验不限"
                            
                            # 创建职位信息字典
                            job_info = {
                                'title': title,
                                'company': company,
                                'salary': salary,
                                'location': location,
                                'experience': experience,
                                'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'keyword': keyword  # 添加搜索关键词
                            }
                            
                            # 将职位信息添加到列表
                            self.jobs.append(job_info)
                            total_scraped += 1
                            
                        except Exception as e:
                            print(f"  解析职位信息出错: {str(e)}")
                    
                    # 打印进度
                    print(f"  第 {page} 页已爬取，当前共 {total_scraped} 条职位")
                    
                    # 随机延迟，避免被封IP
                    time.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    print(f"爬取出错: {str(e)}")
            
            print(f"关键词 '{keyword}' 爬取完成")
        
        print(f"所有关键词爬取完成，共获取 {total_scraped} 条职位信息")
        return total_scraped

    def scrape_zhipin_with_selenium(self, keywords=None, city='101010100', pages=2):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        # 设置Chrome选项
        options = Options()
        # options.add_argument('--headless')  # 无头模式（先不用，方便调试）
        options.add_argument('--disable-blink-features=AutomationControlled')  # 避免被检测为自动化工具
        options.add_argument(f'user-agent={self.headers["User-Agent"]}')
        
        # 初始化webdriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        total_scraped = 0
        
        if keywords is None:
            keywords = self.default_keywords
        
        try:
            # 先访问主页，可能需要登录
            driver.get("https://www.zhipin.com/")
            input("请在浏览器中登录BOSS直聘，然后按Enter继续...")
            
            for keyword in keywords:
                print(f"正在爬取关键词: {keyword}")
                
                for page in range(1, pages + 1):
                    try:
                        print(f"  爬取第 {page} 页...")
                        url = f"https://www.zhipin.com/web/geek/job?query={keyword}&city={city}&page={page}"
                        driver.get(url)
                        
                        # 等待职位列表加载
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".job-list-box"))
                        )
                        
                        # 给页面一点时间完全加载
                        time.sleep(2)
                        
                        # 获取职位列表
                        job_items = driver.find_elements(By.CSS_SELECTOR, '.job-list-box .job-card-wrapper')
                        
                        if not job_items:
                            print("  未找到职位信息，可能是选择器变化")
                            # 尝试其他可能的选择器
                            job_items = driver.find_elements(By.CSS_SELECTOR, '.job-list-box li')
                        
                        if not job_items:
                            print("  仍未找到职位信息，请检查网页结构")
                            # 保存页面源码以便调试
                            with open(f"debug_page_{keyword}_{page}.html", "w", encoding="utf-8") as f:
                                f.write(driver.page_source)
                            break
                        
                        print(f"  找到 {len(job_items)} 个职位")
                        
                        # 解析每个职位
                        for job_item in job_items:
                            try:
                                job_info = {}
                                
                                # 根据您截图中的实际结构调整选择器
                                job_info['title'] = job_item.find_element(By.CSS_SELECTOR, '.job-title').text.strip()
                                job_info['salary'] = job_item.find_element(By.CSS_SELECTOR, '.salary').text.strip()
                                job_info['company'] = job_item.find_element(By.CSS_SELECTOR, '.company-name').text.strip()
                                job_info['location'] = job_item.find_element(By.CSS_SELECTOR, '.job-area').text.strip()
                                
                                # 尝试获取经验要求
                                try:
                                    job_info['experience'] = job_item.find_element(By.CSS_SELECTOR, '.job-info span:nth-child(1)').text.strip()
                                except:
                                    job_info['experience'] = "未知"
                                
                                job_info['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                job_info['keyword'] = keyword
                                
                                self.jobs.append(job_info)
                                total_scraped += 1
                                print(f"    已爬取: {job_info['title']} - {job_info['company']}")
                                
                            except Exception as e:
                                print(f"  解析职位信息出错: {str(e)}")
                        
                        print(f"  第 {page} 页已爬取，当前共 {total_scraped} 条职位")
                        time.sleep(random.uniform(3, 5))  # 随机延迟
                        
                    except Exception as e:
                        print(f"爬取页面出错: {str(e)}")
                    
                print(f"关键词 '{keyword}' 爬取完成")
                
        except Exception as e:
            print(f"爬取过程异常: {str(e)}")
        finally:
            driver.quit()
            
        print(f"所有关键词爬取完成，共获取 {total_scraped} 条职位信息")
        return total_scraped

    def save_data(self):
        """保存爬取的数据"""
        if not self.jobs:
            print("没有数据可保存")
            return False
            
        # 使用数据管理器保存数据
        total_count = self.data_manager.save_jobs(self.jobs)
        
        # 导出当前爬取数据为CSV (可选)
        snapshot_csv = os.path.join(self.data_dir, f'jobs_snapshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        with open(snapshot_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=self.jobs[0].keys())
            writer.writeheader()
            writer.writerows(self.jobs)
            
        return total_count
    
    def print_stats(self):
        """打印数据统计信息"""
        stats = self.data_manager.get_stats()
        print("\n=== 数据统计 ===")
        print(f"总记录数: {stats['total_records']}")
        print(f"最早记录: {stats['earliest_record']}")
        print(f"最近更新: {stats['last_update']}")

def main():
    scraper = ZhipinScraper()
    
    try:
        print("开始爬取BOSS直聘网站职位数据...")
        
        # 提示用户选择爬取模式
        mode = input("请选择爬取模式 (1:真实爬取, 2:模拟数据): ")
        
        if mode == "1":
            # 询问用户是否要自定义爬取参数
            custom = input("是否要自定义爬取参数? (y/n): ").lower()
            
            if custom == 'y':
                # 自定义爬取参数
                keywords_input = input("请输入搜索关键词，用英文逗号分隔 (留空使用默认关键词): ")
                keywords = [k.strip() for k in keywords_input.split(',')] if keywords_input.strip() else None
                
                city_input = input("请输入城市 (北京/上海/广州/深圳/杭州/成都，留空默认为北京): ")
                city_code = '101010100'  # 默认北京
                if city_input.strip() in ['北京', '上海', '广州', '深圳', '杭州', '成都']:
                    city_maps = {
                        '北京': '101010100',
                        '上海': '101020100',
                        '广州': '101280100',
                        '深圳': '101280600',
                        '杭州': '101210100',
                        '成都': '101270100'
                    }
                    city_code = city_maps[city_input.strip()]
                
                pages = int(input("请输入每个关键词爬取的页数 (默认2): ") or 2)
                
                # 执行爬取 - 使用Selenium方法
                scraper.scrape_zhipin_with_selenium(keywords=keywords, city=city_code, pages=pages)
            else:
                # 使用默认参数爬取 - 使用Selenium方法
                scraper.scrape_zhipin_with_selenium()
        else:
            # 生成模拟数据
            print("使用模拟数据代替实际爬取...")
            count = int(input("请输入要生成的模拟数据条数 (默认50): ") or 50)
            scraper.generate_mock_data(count)
        
        # 保存结果
        scraper.save_data()
        
        # 打印统计信息
        scraper.print_stats()
        
    except Exception as e:
        print(f"爬取过程出错: {str(e)}")
        print("切换到模拟数据模式...")
        scraper.generate_mock_data(50)
        scraper.save_data()
        scraper.print_stats()
    
    print("\n所有数据都将存储在集中的数据文件中，可以随时使用data_analysis.py进行分析。")

if __name__ == "__main__":
    main() 