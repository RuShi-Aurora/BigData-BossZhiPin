import os
import json
import csv
from datetime import datetime

class DataManager:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.jobs_file = os.path.join(data_dir, 'all_jobs.json')
        
        # 确保数据目录存在
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # 确保主数据文件存在
        if not os.path.exists(self.jobs_file):
            with open(self.jobs_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def save_jobs(self, jobs, create_snapshot=True):
        """
        保存职位数据到主文件，并可选择创建快照
        
        Args:
            jobs: 要保存的职位数据列表
            create_snapshot: 是否创建数据快照文件
        """
        # 读取现有数据
        existing_jobs = self.load_jobs()
        
        # 为新数据添加爬取时间戳（如果没有）
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for job in jobs:
            if 'crawl_time' not in job:
                job['crawl_time'] = timestamp
        
        # 将新数据添加到现有数据中
        all_jobs = existing_jobs + jobs
        
        # 保存到主文件
        with open(self.jobs_file, 'w', encoding='utf-8') as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=4)
            
        # 创建数据快照（如果需要）
        if create_snapshot:
            snapshot_file = os.path.join(self.data_dir, f'jobs_snapshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, ensure_ascii=False, indent=4)
                
        print(f"已将 {len(jobs)} 条新职位数据添加到数据库，总计 {len(all_jobs)} 条")
        return len(all_jobs)
    
    def load_jobs(self):
        """加载所有职位数据"""
        try:
            with open(self.jobs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载数据时出错: {str(e)}")
            return []
    
    def export_to_csv(self, filename=None):
        """导出所有数据为CSV格式"""
        jobs = self.load_jobs()
        if not jobs:
            print("没有数据可导出")
            return False
            
        if filename is None:
            filename = os.path.join(self.data_dir, f'jobs_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
            
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
            writer.writeheader()
            writer.writerows(jobs)
            
        print(f"已将 {len(jobs)} 条数据导出到 {filename}")
        return True
    
    def get_stats(self):
        """获取数据统计信息"""
        jobs = self.load_jobs()
        stats = {
            "total_records": len(jobs),
            "last_update": max([job.get('crawl_time', '') for job in jobs]) if jobs else 'N/A',
            "earliest_record": min([job.get('crawl_time', '') for job in jobs]) if jobs else 'N/A'
        }
        return stats 