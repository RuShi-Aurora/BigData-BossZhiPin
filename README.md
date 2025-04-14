# 职位数据爬取与分析系统

这是一个用于爬取职位信息并进行数据分析的系统。本系统采用模块化设计，包含数据爬取、数据管理和数据分析三个核心模块，可以对职位数据进行收集、存储和可视化分析。

## 模拟数据说明

**重要提示：当前版本使用的是模拟生成的数据，而非实际爬取的数据。**

### 为何使用模拟数据？

当前版本选择使用模拟数据而不是真实爬取的原因如下：

1. **避免依赖问题**：真实爬取需要安装额外的依赖包如requests、beautifulsoup4等，使用模拟数据可以降低系统运行门槛
2. **避免网站反爬限制**：许多招聘网站有严格的反爬虫机制，包括IP封禁、验证码等，使用模拟数据可以避免这些问题
3. **便于测试和演示**：模拟数据可以快速生成大量样本，便于系统功能测试和演示
4. **合规性考虑**：爬取某些网站可能涉及法律和使用条款问题，使用模拟数据避免了这些潜在风险

### 模拟数据与真实爬取的区别

模拟数据是通过代码随机生成的，而非从实际网站获取：

```python
# 模拟数据生成代码片段
job_info = {
    'title': random.choice(job_titles),  # 从预定义列表随机选择
    'company': random.choice(companies),
    'salary': random.choice(salaries),
    'location': random.choice(locations),
    'experience': random.choice(experiences),
    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}
```

而真实爬取会包含以下步骤：

```python
# 真实爬取的伪代码示例
def get_job_data(page=1):
    url = f"https://www.example.com/jobs?page={page}"
    response = requests.get(url, headers=self.headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    job_items = soup.find_all('div', class_='job-card')
    
    for item in job_items:
        job_info = {
            'title': item.find('div', class_='job-title').text.strip(),
            # ... 其他字段的提取逻辑
        }
        self.jobs.append(job_info)
```

### 未来实现真实爬取的计划

系统设计时已考虑到未来转换为真实爬取的需求，只需替换`generate_mock_data()`方法为实际的爬取方法即可，无需改变数据存储和分析部分的代码。

若要实现真实爬取，需要：
1. 安装必要的依赖：`requests`、`beautifulsoup4`等
2. 实现网站特定的爬取逻辑
3. 添加反爬处理机制
4. 考虑数据清洗和验证流程

## 文件结构及功能说明

### 核心文件

| 文件名 | 类型 | 功能描述 |
|--------|------|----------|
| `zhipin_scraper.py` | 爬虫模块 | 用于从招聘网站爬取职位数据，当前版本使用模拟数据进行演示 |
| `data_manager.py` | 数据管理模块 | 负责数据的存储、检索和管理，确保数据的一致性和可用性 |
| `data_analysis.py` | 数据分析模块 | 加载并分析职位数据，生成各类可视化图表和分析报告 |
| `requirements.txt` | 依赖文件 | 列出项目所需的Python包依赖 |
| `requirements_analysis.txt` | 依赖文件 | 列出数据分析所需的Python包依赖 |

### 目录结构

| 目录名 | 用途 |
|--------|------|
| `data/` | 存储原始爬取数据 |
| `eyes/` | 存储可视化分析结果 |

### 数据文件

| 文件名 | 位置 | 描述 |
|--------|------|------|
| `all_jobs.json` | `data/` | 集中存储所有爬取的职位数据的主数据文件 |
| `jobs_snapshot_*.json` | `data/` | 每次爬取的单次结果快照，用于备份和追踪 |
| `salary_distribution.png` | `eyes/` | 薪资分布分析图表 |
| `job_market_overview.png` | `eyes/` | 职位市场概览图表 |
| `skills_analysis.png` | `eyes/` | 技能需求分析图表 |
| `skills_analysis_cloud.png` | `eyes/` | 技能需求词云图 |
| `salary_vs_exp_edu.png` | `eyes/` | 薪资与经验、学历关系分析图 |
| `job_analysis_dashboard.html` | `eyes/` | 交互式仪表盘，包含所有分析结果 |

## 数据来源说明

### 当前模拟数据来源

当前版本使用模拟数据进行演示，数据生成规则如下：

1. **职位标题**：从预定义列表中随机选择，包括：
   - Python开发工程师
   - 数据分析师
   - 前端开发工程师
   - Java开发工程师
   - 人工智能工程师

2. **公司名称**：从知名互联网公司列表中随机选择，包括：
   - 腾讯
   - 阿里巴巴
   - 百度
   - 字节跳动
   - 美团
   - 京东
   - 华为
   - 小米

3. **薪资范围**：从常见薪资范围中随机选择，格式为"最低K-最高K"，如：
   - 15K-25K
   - 20K-40K
   - 30K-50K
   - 25K-35K
   - 18K-30K

4. **工作地点**：从主要一线和新一线城市中随机选择，包括：
   - 北京
   - 上海
   - 深圳
   - 广州
   - 杭州
   - 成都

5. **工作经验要求**：从常见经验要求中随机选择，包括：
   - 1-3年
   - 3-5年
   - 5-10年
   - 不限

6. **数据时间戳**：使用生成时的实际时间，格式为"YYYY-MM-DD HH:MM:SS"

### 预期真实数据来源

在实际应用中，系统可配置为从以下招聘网站获取真实职位数据：

1. **BOSS直聘**（主要目标）：
   - 数据接口：`https://www.zhipin.com/web/geek/job-recommend`
   - 爬取频率：每日更新
   - 数据格式：JSON/HTML混合
   - 需处理的反爬机制：Cookie验证、IP限制、User-Agent检测

2. **拉勾网**（备选）：
   - 数据接口：`https://www.lagou.com/jobs/positionAjax.json`
   - 爬取方式：API + 网页解析
   - 特点：提供较为详细的职位技能要求和公司融资情况

3. **智联招聘**（备选）：
   - 爬取方式：网页解析
   - 特点：覆盖范围广，包含更多传统行业职位

4. **猎聘网**（高端职位补充）：
   - 特点：包含更多高薪职位和管理岗位
   - 适合分析高端人才市场需求

### 数据获取策略

实际数据获取将采用以下策略：

1. **定时爬取**：每日凌晨自动运行爬虫程序，避开网站高峰期
2. **增量爬取**：仅爬取新发布的职位信息，减少重复数据
3. **多点爬取**：通过多个代理IP轮换爬取，避免被封禁
4. **请求延迟**：每次请求间随机延迟1-3秒，模拟人工浏览行为
5. **数据验证**：对爬取的数据进行格式验证和清洗，确保数据质量

### 数据结构

无论是模拟数据还是真实爬取的数据，都遵循以下JSON结构：

```json
{
  "job_name": "Python开发工程师",   // 职位标题
  "company_name": "腾讯",           // 公司名称
  "salary": "20K-40K",        // 薪资范围
  "job_area": "深圳",          // 工作地点
  "job_requirements": ["3-5年", "本科", "Python", "Django"],  // 工作要求
  "crawl_time": "2023-06-15 14:22:18"  // 爬取时间
}
```

真实数据爬取时，可能会扩展以下字段：

```json
{
  // ... 基础字段 ...
  "education": "本科",          // 学历要求
  "company_type": "上市公司",    // 公司类型
  "company_size": "2000人以上",  // 公司规模
  "industry": "互联网",         // 所属行业
  "skills": ["Python", "Django", "MySQL"],  // 技能要求
  "benefits": ["五险一金", "年终奖", "弹性工作"],  // 公司福利
  "job_description": "负责公司核心业务系统的开发...",  // 职位描述
  "source_url": "https://www.zhipin.com/job_detail/xxx"  // 数据来源URL
}
```

## 模块详细说明

### 1. 爬虫模块 (zhipin_scraper.py)

这个模块负责从招聘网站收集职位数据。

**主要功能：**
- 生成模拟职位数据（当前版本）
- 将数据保存到集中数据文件
- 创建数据快照
- 提供数据统计信息

**核心类和方法：**
- `ZhipinScraper`: 主爬虫类
  - `generate_mock_data()`: 生成模拟数据
  - `save_data()`: 保存爬取的数据
  - `print_stats()`: 打印数据统计信息

### 2. 数据管理模块 (data_manager.py)

这个模块处理数据的存储和检索操作，是连接爬虫和分析模块的桥梁。

**主要功能：**
- 管理集中数据文件
- 加载和保存职位数据
- 生成数据快照
- 提供数据统计信息

**核心类和方法：**
- `DataManager`: 数据管理类
  - `save_jobs()`: 将新数据添加到集中文件
  - `load_jobs()`: 从集中文件加载所有数据
  - `export_to_csv()`: 将数据导出为CSV格式
  - `get_stats()`: 获取数据统计信息

### 3. 数据分析模块 (data_analysis.py)

这个模块负责对收集的职位数据进行可视化分析和展示。

**主要功能：**
- 数据加载与预处理
- 薪资分布分析
- 职位市场概览
- 技能需求分析
- 薪资与经验、学历关系分析
- 生成交互式可视化仪表盘

**核心类和方法：**
- `JobMarketAnalyzer`: 职位市场分析器类
  - `load_data()`: 从JSON文件加载数据
  - `process_data()`: 数据清洗和预处理
  - `_parse_salary()`: 解析薪资信息
  - `_extract_requirements()`: 提取工作要求中的经验、学历和技能
  - `salary_distribution_analysis()`: 薪资分布分析
  - `job_market_overview()`: 职位市场概览分析
  - `skills_analysis()`: 技能需求分析及词云生成
  - `salary_vs_experience_education()`: 薪资与经验、学历关系分析
  - `generate_interactive_dashboard()`: 生成交互式仪表盘
  - `run_full_analysis()`: 运行完整分析流程

**主要可视化内容：**
1. **薪资分布分析**：
   - 薪资分布密度曲线
   - 各城市薪资分布箱线图

2. **职位市场概览**：
   - 招聘职位数量前15的公司
   - 各城市职位数量分布
   - 学历要求分布
   - 工作经验要求分布

3. **技能需求分析**：
   - 职位技能需求Top20柱状图
   - 技能需求词云图

4. **薪资与经验、学历关系**：
   - 工作经验与平均薪资关系图
   - 学历要求与平均薪资关系图

5. **交互式仪表盘**：
   - 综合展示上述所有分析内容的HTML交互式页面
   - 支持数据筛选、放大和导出等交互功能

## 系统流程

1. **数据爬取阶段**：
   - 运行爬虫收集职位数据
   - 数据被添加到集中存储文件
   - 同时创建当次爬取的数据快照
   
2. **数据分析阶段**：
   - 从集中文件加载所有历史数据
   - 对数据进行清洗和预处理
   - 生成各类分析图表
   - 创建交互式仪表盘
   - 所有结果保存到eyes目录

## 使用方法

### 1. 环境准备

首先，确保您的系统安装了Python 3.6+，然后安装必要的依赖库：

```bash
# 安装基本依赖
pip install -r requirements.txt

# 安装数据分析依赖
pip install -r requirements_analysis.txt
```

或者直接安装所有必要的分析依赖：

```bash
pip install pandas numpy matplotlib seaborn plotly wordcloud scikit-learn
```

### 2. 爬取数据

运行爬虫程序收集职位数据：

```bash
python zhipin_scraper.py
```

每次运行都会：
- 生成新的模拟职位数据（在实际使用中，这里会从网站爬取真实数据）
- 将这些数据添加到集中存储文件 `data/all_jobs.json` 中
- 创建一个包含本次爬取数据的快照文件
- 显示当前数据库中的总记录数等统计信息

### 3. 分析数据

运行分析程序对所有收集的数据进行分析：

```bash
# 默认分析
python data_analysis.py

# 指定数据源和输出目录
python data_analysis.py --data data/all_jobs.json --output eyes

# 仅生成交互式仪表盘
python data_analysis.py --interactive
```

分析程序会：
- 从集中存储文件加载所有历史数据
- 进行数据清洗和预处理
- 生成以下分析图表：
  - 薪资分布密度曲线和各城市薪资分布箱线图
  - 职位市场概览（公司、城市、学历、经验分布）
  - 技能需求分析和词云
  - 薪资与经验、学历关系分析
- 生成交互式仪表盘
- 所有分析结果保存在 `eyes/` 目录中
  
### 4. 查看分析结果

分析结果保存在 `eyes/` 目录中：
- 各类PNG格式的分析图表
- `job_analysis_dashboard.html` 交互式仪表盘文件

可以使用浏览器打开交互式仪表盘文件，体验更丰富的数据探索功能。

## 注意事项

1. **关于模拟数据**：
   当前版本的爬虫使用模拟数据代替实际爬取，以避免对外部依赖的需求。如需实际爬取真实数据，需要修改爬虫代码中的相关部分，添加实际网站的爬取逻辑。

2. **中文显示问题**：
   系统已优化中文字体支持，会自动查找系统中的中文字体。如果遇到中文显示问题，可以尝试安装SimHei或Microsoft YaHei字体。

3. **数据累积**：
   系统设计为支持数据随时间累积，每次爬取的新数据会被添加到现有数据中，而不是替换，这样可以进行长期的数据趋势分析。

4. **交互式仪表盘**：
   交互式仪表盘使用Plotly生成，提供比静态图表更丰富的交互体验，包括缩放、悬停查看详情、筛选等功能。

5. **扩展性**：
   系统采用模块化设计，可以方便地扩展新的分析功能或修改爬取逻辑，如添加新的分析图表或支持其他招聘网站。 