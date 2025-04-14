import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import re
from collections import Counter
from datetime import datetime
import matplotlib.font_manager as fm
import os
from data_manager import DataManager
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap
from wordcloud import WordCloud
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

class JobMarketAnalyzer:
    def __init__(self, data_path='data/all_jobs.json'):
        """初始化职位市场分析器"""
        self.data_path = data_path
        self.data_manager = DataManager()
        self.df = None
        self.load_data()
        self.process_data()
        
    def load_data(self):
        """从JSON文件加载数据到DataFrame"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                jobs_data = json.load(f)
            
            self.df = pd.DataFrame(jobs_data)
            print(f"成功加载 {len(self.df)} 条职位数据")
        except Exception as e:
            print(f"加载数据失败: {str(e)}")
            # 如果加载失败，尝试从DataManager加载
            jobs_data = self.data_manager.load_jobs()
            self.df = pd.DataFrame(jobs_data)
            print(f"从DataManager成功加载 {len(self.df)} 条职位数据")
    
    def process_data(self):
        """处理和清洗数据"""
        if self.df is None or len(self.df) == 0:
            print("没有数据可处理")
            return
        
        # 重命名列以确保一致性
        if 'title' in self.df.columns and 'job_name' not in self.df.columns:
            self.df.rename(columns={'title': 'job_name'}, inplace=True)
        
        if 'location' in self.df.columns and 'job_area' not in self.df.columns:
            self.df.rename(columns={'location': 'job_area'}, inplace=True)
        
        # 提取薪资上下限
        self.df['salary_min'] = 0
        self.df['salary_max'] = 0
        self.df['salary_avg'] = 0
        self.df['salary_unit'] = 'K'
        self.df['salary_months'] = 12
        
        # 从薪资字符串中提取数值
        for idx, row in self.df.iterrows():
            if 'salary' in row and row['salary']:
                self._parse_salary(idx, row['salary'])
                
        # 解析工作区域
        if 'job_area' in self.df.columns:
            self.df['city'] = self.df['job_area'].apply(lambda x: x.split('·')[0] if '·' in str(x) else x)
            self.df['district'] = self.df['job_area'].apply(lambda x: x.split('·')[1] if '·' in str(x) and len(x.split('·')) > 1 else '')
        
        # 解析工作要求
        if 'job_requirements' in self.df.columns:
            self._extract_requirements()
        
        print("数据处理完成")
    
    def _parse_salary(self, idx, salary_str):
        """解析薪资字符串"""
        try:
            # 匹配薪资范围和单位
            pattern = r'(\d+)-(\d+)([KkWw万])'
            match = re.search(pattern, str(salary_str))
            
            if match:
                min_salary = int(match.group(1))
                max_salary = int(match.group(2))
                unit = match.group(3).upper()
                
                self.df.at[idx, 'salary_min'] = min_salary
                self.df.at[idx, 'salary_max'] = max_salary
                self.df.at[idx, 'salary_avg'] = float((min_salary + max_salary) / 2)
                self.df.at[idx, 'salary_unit'] = 'W' if unit in ['W', 'w', '万'] else 'K'
                
                # 检查是否有额外月薪信息
                months_pattern = r'(\d+)薪'
                months_match = re.search(months_pattern, str(salary_str))
                if months_match:
                    self.df.at[idx, 'salary_months'] = int(months_match.group(1))
        except Exception as e:
            print(f"解析薪资失败 '{salary_str}': {str(e)}")
    
    def _extract_requirements(self):
        """从工作要求中提取经验、学历等信息"""
        # 初始化新列
        self.df['experience'] = ''
        self.df['education'] = ''
        self.df['skills'] = ''
        
        # 经验和学历的模式
        exp_patterns = [r'(\d+)-(\d+)年', r'(\d+)年以上']
        edu_keywords = ['大专', '本科', '硕士', '博士', '学历不限']
        
        # 逐行处理
        for idx, row in self.df.iterrows():
            if 'job_requirements' in row and isinstance(row['job_requirements'], list):
                reqs = row['job_requirements']
                
                # 提取经验
                for req in reqs:
                    for pattern in exp_patterns:
                        if re.search(pattern, str(req)):
                            self.df.at[idx, 'experience'] = req
                
                # 提取学历
                for req in reqs:
                    if any(edu in str(req) for edu in edu_keywords):
                        self.df.at[idx, 'education'] = req
                
                # 其他视为技能
                skills = [req for req in reqs 
                          if req != self.df.at[idx, 'experience'] and 
                          req != self.df.at[idx, 'education']]
                self.df.at[idx, 'skills'] = skills
    
    def salary_distribution_analysis(self, save_path=None):
        """薪资分布分析"""
        if self.df is None or 'salary_avg' not in self.df.columns:
            print("缺少薪资数据")
            return
        
        # 创建画布
        plt.figure(figsize=(14, 8))
        
        # 设置颜色主题
        colors = sns.color_palette("viridis", 3)
        
        # 创建子图
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
        
        # 绘制KDE图
        sns.kdeplot(data=self.df, x='salary_avg', fill=True, ax=ax1, color=colors[0])
        ax1.set_title('薪资分布密度曲线', fontsize=16)
        ax1.set_xlabel('平均月薪 (K)', fontsize=14)
        ax1.set_ylabel('密度', fontsize=14)
        
        # 绘制箱线图 - 按城市分组
        if 'city' in self.df.columns:
            # 获取薪资最高的前10个城市
            top_cities = self.df.groupby('city')['salary_avg'].mean().nlargest(8).index
            city_data = self.df[self.df['city'].isin(top_cities)]
            
            sns.boxplot(x='city', y='salary_avg', data=city_data, ax=ax2, palette="viridis", hue='city', legend=False)
            ax2.set_title('各城市薪资分布箱线图', fontsize=16)
            ax2.set_xlabel('城市', fontsize=14)
            ax2.set_ylabel('平均月薪 (K)', fontsize=14)
            ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # 保存或显示
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"薪资分布图已保存到 {save_path}")
        else:
            plt.show()
        
        plt.close()

    def job_market_overview(self, save_path=None):
        """职位市场概览"""
        if self.df is None:
            print("没有数据可分析")
            return
        
        # 创建画布
        fig, axes = plt.subplots(2, 2, figsize=(20, 16))
        
        # 1. 职位数量前15的公司
        company_counts = self.df['company_name'].value_counts().head(15)
        company_df = pd.DataFrame({'company': company_counts.index, 'count': company_counts.values})
        sns.barplot(x='count', y='company', data=company_df, ax=axes[0, 0], palette="viridis")
        axes[0, 0].set_title('招聘职位数量前15的公司', fontsize=16)
        axes[0, 0].set_xlabel('职位数量', fontsize=14)
        
        # 2. 各城市职位数量
        if 'city' in self.df.columns:
            city_counts = self.df['city'].value_counts().head(10)
            city_df = pd.DataFrame({'city': city_counts.index, 'count': city_counts.values})
            sns.barplot(x='count', y='city', data=city_df, ax=axes[0, 1], palette="viridis")
            axes[0, 1].set_title('各城市职位数量分布', fontsize=16)
            axes[0, 1].set_xlabel('职位数量', fontsize=14)
        
        # 3. 学历要求分布
        if 'education' in self.df.columns:
            edu_counts = self.df['education'].value_counts().head(10)
            edu_df = pd.DataFrame({'education': edu_counts.index, 'count': edu_counts.values})
            sns.barplot(x='count', y='education', data=edu_df, ax=axes[1, 0], palette="viridis")
            axes[1, 0].set_title('学历要求分布', fontsize=16)
            axes[1, 0].set_xlabel('职位数量', fontsize=14)
        
        # 4. 工作经验要求分布
        if 'experience' in self.df.columns:
            exp_counts = self.df['experience'].value_counts().head(10)
            exp_df = pd.DataFrame({'experience': exp_counts.index, 'count': exp_counts.values})
            sns.barplot(x='count', y='experience', data=exp_df, ax=axes[1, 1], palette="viridis")
            axes[1, 1].set_title('工作经验要求分布', fontsize=16)
            axes[1, 1].set_xlabel('职位数量', fontsize=14)
        
        plt.tight_layout()
        
        # 保存或显示
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"职位市场概览已保存到 {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def skills_analysis(self, save_path=None):
        """技能需求分析"""
        if self.df is None or 'skills' not in self.df.columns:
            print("缺少技能数据")
            return
        
        # 提取所有技能并计数
        all_skills = []
        for skills_list in self.df['skills']:
            if isinstance(skills_list, list):
                all_skills.extend(skills_list)
        
        skill_counter = Counter(all_skills)
        top_skills = skill_counter.most_common(20)
        
        # 转换为DataFrame
        skills_df = pd.DataFrame(top_skills, columns=['skill', 'count'])
        
        # 创建画布
        plt.figure(figsize=(14, 8))
        
        # 绘制技能需求柱状图
        ax = sns.barplot(x='count', y='skill', data=skills_df, palette="viridis")
        ax.set_title('职位技能需求Top20', fontsize=16)
        ax.set_xlabel('需求数量', fontsize=14)
        ax.set_ylabel('技能', fontsize=14)
        
        plt.tight_layout()
        
        # 保存或显示
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"技能需求分析已保存到 {save_path}")
        else:
            plt.show()
        
        plt.close()
        
        # 创建词云
        if len(all_skills) > 0:
            plt.figure(figsize=(14, 10))
            
            # 准备词云文本
            text = ' '.join(all_skills)
            
            try:
                # 修复字体路径问题，设置为默认字体
                font_path = None
                try:
                    # 尝试使用Windows默认字体
                    import matplotlib.font_manager as fm
                    font_paths = fm.findSystemFonts()
                    # 尝试找SimHei字体或任何中文字体
                    for path in font_paths:
                        if 'simhei' in path.lower() or 'msyh' in path.lower():
                            font_path = path
                            break
                except:
                    pass
                
                # 设置词云参数
                wordcloud = WordCloud(
                    font_path=font_path,  # 使用找到的系统字体或None使用默认字体
                    width=1200, 
                    height=800,
                    background_color='white',
                    max_words=100,
                    colormap='viridis'
                ).generate(text)
                
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis('off')
                plt.title('技能需求词云', fontsize=20)
                
                # 保存或显示
                if save_path:
                    cloud_path = save_path.replace('.png', '_cloud.png')
                    plt.savefig(cloud_path, dpi=300, bbox_inches='tight')
                    print(f"技能需求词云已保存到 {cloud_path}")
                else:
                    plt.show()
            except Exception as e:
                print(f"生成词云失败: {str(e)}")
                print("跳过词云生成，继续分析...")
            
            plt.close()
    
    def salary_vs_experience_education(self, save_path=None):
        """薪资与经验、学历的关系分析"""
        if self.df is None or 'salary_avg' not in self.df.columns:
            print("缺少薪资数据")
            return
        
        # 创建画布
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
        
        # 分析经验与薪资的关系
        if 'experience' in self.df.columns and self.df['experience'].nunique() > 1:
            # 提取经验年限
            def extract_exp_years(exp_str):
                if pd.isna(exp_str) or exp_str == '':
                    return 'Unknown'
                    
                pattern1 = r'(\d+)-(\d+)年'  # 匹配范围，如"1-3年"
                pattern2 = r'(\d+)年以上'    # 匹配"X年以上"
                
                match1 = re.search(pattern1, str(exp_str))
                match2 = re.search(pattern2, str(exp_str))
                
                if match1:
                    return f"{match1.group(1)}-{match1.group(2)}年"
                elif match2:
                    return f"{match2.group(1)}年以上"
                else:
                    return str(exp_str)
            
            self.df['exp_category'] = self.df['experience'].apply(extract_exp_years)
            
            # 计算每个经验类别的平均薪资
            exp_salary = self.df.groupby('exp_category')['salary_avg'].mean().reset_index()
            
            # 根据经验排序（复杂一点，需要自定义排序）
            def exp_sort_key(exp):
                if '以上' in exp:
                    return int(re.search(r'(\d+)', exp).group(1)) * 100
                elif '-' in exp:
                    start, end = re.search(r'(\d+)-(\d+)', exp).groups()
                    return (int(start) + int(end)) / 2
                else:
                    return 0
            
            exp_salary['sort_key'] = exp_salary['exp_category'].apply(exp_sort_key)
            exp_salary = exp_salary.sort_values('sort_key')
            
            # 绘制经验与薪资的关系 - 修复FutureWarning
            sns.barplot(x='exp_category', y='salary_avg', data=exp_salary, ax=ax1, palette="viridis")
            ax1.set_title('工作经验与平均薪资关系', fontsize=16)
            ax1.set_xlabel('工作经验', fontsize=14)
            ax1.set_ylabel('平均月薪 (K)', fontsize=14)
            ax1.tick_params(axis='x', rotation=45)
        
        # 分析学历与薪资的关系
        if 'education' in self.df.columns and self.df['education'].nunique() > 1:
            # 计算每个学历类别的平均薪资
            edu_salary = self.df.groupby('education')['salary_avg'].mean().reset_index()
            
            # 定义学历排序
            edu_order = ['学历不限', '大专', '本科', '硕士', '博士']
            
            # 筛选有效学历
            valid_edu = [e for e in edu_order if e in edu_salary['education'].values]
            edu_salary = edu_salary[edu_salary['education'].isin(valid_edu)]
            
            # 绘制学历与薪资的关系
            if len(edu_salary) > 0:
                # 自定义排序
                edu_order_dict = {edu: i for i, edu in enumerate(edu_order)}
                edu_salary['sort_key'] = edu_salary['education'].map(edu_order_dict)
                edu_salary = edu_salary.sort_values('sort_key')
                
                # 修复FutureWarning
                sns.barplot(x='education', y='salary_avg', data=edu_salary, ax=ax2, palette="viridis")
                ax2.set_title('学历要求与平均薪资关系', fontsize=16)
                ax2.set_xlabel('学历要求', fontsize=14)
                ax2.set_ylabel('平均月薪 (K)', fontsize=14)
                ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # 保存或显示
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"薪资与经验、学历关系分析图已保存到 {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def generate_interactive_dashboard(self, output_file='job_analysis_dashboard.html'):
        """生成交互式仪表盘"""
        if self.df is None:
            print("没有数据可分析")
            return
        
        # 创建子图布局
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                '薪资分布', 
                '各城市平均薪资',
                '招聘职位数量前10的公司',
                '技能需求TOP15'
            ),
            specs=[
                [{"type": "scatter"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "bar"}]
            ]
        )
        
        # 1. 薪资分布图
        fig.add_trace(
            go.Histogram(
                x=self.df['salary_avg'],
                nbinsx=20,
                marker_color='rgba(73, 43, 174, 0.6)',
                name='薪资分布'
            ),
            row=1, col=1
        )
        
        # 添加薪资密度曲线
        salary_range = np.linspace(self.df['salary_avg'].min(), self.df['salary_avg'].max(), 100)
        kde = sns.kdeplot(self.df['salary_avg']).get_lines()[0].get_data()
        fig.add_trace(
            go.Scatter(
                x=kde[0],
                y=kde[1],
                mode='lines',
                line=dict(color='rgba(220, 57, 18, 0.8)', width=3),
                name='薪资密度'
            ),
            row=1, col=1
        )
        
        # 2. 各城市平均薪资
        if 'city' in self.df.columns:
            city_salary = self.df.groupby('city')['salary_avg'].mean().nlargest(10).reset_index()
            fig.add_trace(
                go.Bar(
                    y=city_salary['city'],
                    x=city_salary['salary_avg'],
                    orientation='h',
                    marker_color='rgba(33, 158, 188, 0.8)',
                    name='城市平均薪资'
                ),
                row=1, col=2
            )
        
        # 3. 招聘职位数量前10的公司
        company_counts = self.df['company_name'].value_counts().head(10).reset_index()
        company_counts.columns = ['company', 'count']
        fig.add_trace(
            go.Bar(
                y=company_counts['company'],
                x=company_counts['count'],
                orientation='h',
                marker_color='rgba(254, 97, 0, 0.8)',
                name='公司职位数'
            ),
            row=2, col=1
        )
        
        # 4. 技能需求分析
        if 'skills' in self.df.columns:
            all_skills = []
            for skills_list in self.df['skills']:
                if isinstance(skills_list, list):
                    all_skills.extend(skills_list)
            
            skill_counter = Counter(all_skills)
            top_skills = skill_counter.most_common(15)
            skills_df = pd.DataFrame(top_skills, columns=['skill', 'count'])
            
            fig.add_trace(
                go.Bar(
                    y=skills_df['skill'],
                    x=skills_df['count'],
                    orientation='h',
                    marker_color='rgba(36, 123, 160, 0.8)',
                    name='技能需求'
                ),
                row=2, col=2
            )
        
        # 更新布局
        fig.update_layout(
            title_text='互联网职位市场分析仪表盘',
            title_font_size=24,
            height=900,
            showlegend=False,
        )
        
        # 保存HTML文件
        fig.write_html(output_file)
        print(f"交互式仪表盘已保存到 {output_file}")
        
    def run_full_analysis(self, output_dir='analysis_results'):
        """运行完整分析并保存结果"""
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 运行各种分析
        self.salary_distribution_analysis(save_path=f"{output_dir}/salary_distribution.png")
        self.job_market_overview(save_path=f"{output_dir}/job_market_overview.png")
        self.skills_analysis(save_path=f"{output_dir}/skills_analysis.png")
        self.salary_vs_experience_education(save_path=f"{output_dir}/salary_vs_exp_edu.png")
        self.generate_interactive_dashboard(output_file=f"{output_dir}/job_analysis_dashboard.html")
        
        print(f"所有分析结果已保存到 {output_dir} 目录")


def main():
    """主函数"""
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='职位数据分析工具')
    parser.add_argument('--data', type=str, default='data/all_jobs.json', help='职位数据JSON文件路径')
    parser.add_argument('--output', type=str, default='eyes', help='分析结果输出目录')
    parser.add_argument('--interactive', action='store_true', help='只生成交互式仪表盘')
    args = parser.parse_args()
    
    # 创建分析器实例
    analyzer = JobMarketAnalyzer(data_path=args.data)
    
    # 根据参数执行分析
    if args.interactive:
        print("生成交互式仪表盘...")
        analyzer.generate_interactive_dashboard(output_file=f"{args.output}/job_analysis_dashboard.html")
    else:
        print("运行完整分析...")
        analyzer.run_full_analysis(output_dir=args.output)
    
    print("分析完成！")


if __name__ == "__main__":
    main()
