# @Date    : 2018-03-16
# @Author  : Harry Mei
# @Link    : https://harrymei.github.io/
# @Version : Python3.4

import requests
import time
import csv
import os
import io
import sys
from pprint import pprint

def log(msg, is_init=False):
	print(msg)
	msg += '\n'
	if is_init:
		with open('./log.txt', 'w') as f:
			f.write(msg)  
	else:
		with open('./log.txt', 'a') as f:
			f.write(msg)  

class BangumiSpider(requests.Session):
	"""docstring for BangumiSpider"""
	def __init__(self, year=0, season=0):
		super(BangumiSpider, self).__init__()
		self.index_url = 'https://bangumi.bilibili.com/web_api/season/index_global'
		self.bangumis = []
		self.bangumis_info = {}
		self.counter = 0
		self.max_num = 3000
		self.data = {
				'page':1,			# 第几页
				'page_size':100,		# 每页的数量
				'version':0, 		# 类型： 全部 正片 剧场版 其他 [0 - 4]
				'is_finish':0,		# 状态： 全部 完结 连载 [0 2 1]
				'start_year':year, 	# 时间： 全部 某一年 [0 xxxx]
				'tag_id':'',		# 风格
				'index_type':0,		# 排序方式: 更新时间 追番人数 开播时间 [0 - 2]
				'index_sort':0,		# 排序类型: 递减 递增 [0 - 1]
				'area':0,			# 地区: 全部 日本 美国 其他 [0 2 3 4]
				'quarter':season,	# 季度： 全部 1月 4月 7月 10月 [0 - 4]
			}
		self.data['page_size'] = int(self.data['page_size']/20)*20
		if self.data['page_size'] < 20: self.data['page_size'] = 20
		self.headers = ['season_id',		# 番剧ID
						'title',			# 番剧名
						'play_count',		# 播放量
						'danmaku_count',	# 弹幕量
						'coins',			# 硬币数
						'favorites',		# 追番数
						'score',			# 评分
						'total_count',		# 总集数
						'week',				# 星期几播出
						'newest_ep_index',	# 最新播放集数
						'is_finish',		# 是否完结
						'area',				# 地区
						'arealimit',		# 地区限制
						'pub_time',			# 播出时间
						'season_status',	# 第季度开始播出
						'copyright',		# 版权
						'tags',				# 标签
						'actor',			# 声优
						]
		try:
			if year == 0: str_year = str(year)
			if season == 0: str_season = str(season)
			self.csv_file = './bangumi_'+str(self.year)+'_'+str(self.seanon)+'.csv'
		except:
			self.csv_file = './bangumi_total.csv'

	def _bangumis_info_fill(self, season_id):
		self.bangumis_info[season_id]['play_count'] = ''
		self.bangumis_info[season_id]['danmaku_count'] = ''
		self.bangumis_info[season_id]['coins'] = ''
		self.bangumis_info[season_id]['score'] = ''
		self.bangumis_info[season_id]['actor'] = []
		self.bangumis_info[season_id]['area'] = ''
		self.bangumis_info[season_id]['copyright'] = ''
		self.bangumis_info[season_id]['arealimit'] = ''
		self.bangumis_info[season_id]['aid'] = ''
		self.bangumis_info[season_id]['tags'] = []
		self.bangumis_info[season_id]['pub_time'] = ''
		self.bangumis_info[season_id]['copyright'] = ''

	def run(self):	
		while self.counter < self.max_num :
			self.bangumis_info.clear()
			self.bangumis.clear()
			json_data = self._get_bangumi_data()
			self.data['page'] += int(self.data['page_size']/20)
			if len(json_data) == 3:
				self._add_bangumi_list(json_data)
				self._get_bangumi_desc()
				self._dump_to_csv()
			else:
				break
		# pprint(self.bangumis_info)

	def _add_bangumi_list(self, json_data):
		items = json_data['result']['list']
		for item in items:
			del item['cover']
			del item['url']
			del item['update_time']
			self.bangumis_info[item['season_id']] = item
			self.bangumis.append(item['season_id'])

	def _add_desc_infor(self, data, season_id):		
		if data is not None:
			data_info = eval(data[data.find('{'):-2])['result']
			self.bangumis_info[season_id]['play_count'] = data_info['play_count']
			self.bangumis_info[season_id]['danmaku_count'] = data_info['danmaku_count']
			self.bangumis_info[season_id]['coins'] = data_info['coins']
			self.bangumis_info[season_id]['actor'] = [actor['actor'] for actor in data_info['actor']]
			self.bangumis_info[season_id]['area'] = data_info['area']
			self.bangumis_info[season_id]['copyright'] = data_info['copyright']
			self.bangumis_info[season_id]['arealimit'] = data_info['arealimit']
			self.bangumis_info[season_id]['aid'] = {episodes['index']:episodes['av_id'] for episodes in data_info['episodes'] }
			self.bangumis_info[season_id]['tags'] = [tag['tag_name'] for tag in data_info['tags']]
			self.bangumis_info[season_id]['pub_time'] = data_info['pub_time']
			self.bangumis_info[season_id]['copyright'] = data_info['copyright']
			self.bangumis_info[season_id]['score'] = data_info['media']['rating']['score']
			self.bangumis_info[season_id]['title'] = data_info['bangumi_title']
		# pprint(self.bangumis_info[season_id])

	def _get_bangumi_desc(self):
		for season_id in self.bangumis:
			url = 'http://bangumi.bilibili.com/jsonp/seasoninfo/'+str(season_id)+'.ver?callback=seasonListCallback'
			# url = 'http://bangumi.bilibili.com/jsonp/seasoninfo/'+str(4294)+'.ver?callback=seasonListCallback'
			time.sleep(0.1)
			self.counter += 1
			self._bangumis_info_fill(season_id)
			try:
				req = self.get(url, timeout = 1)
				req.raise_for_status()
				req.encoding = req.apparent_encoding
				try:
					self._add_desc_infor(req.text, season_id)
				except:
					pass
				log(str(self.counter)+'  Get OK!: '+self.bangumis_info[season_id]['title'])
			except:
				self.bangumis_info[season_id]['title'] = ''
				log('Get data fail!: '+url)
				continue

	def _get_bangumi_data(self):
		try:
			req = self.get(self.index_url, params = self.data, timeout = 1)
			req.raise_for_status()
			req.encoding = req.apparent_encoding
			return req.json()		
		except:
			log('Get bangumi fail!')
			return {}

	def _dump_to_csv(self):
		file_exist = os.path.exists(self.csv_file)
		data_list = list(self.bangumis_info.values())
		with open(self.csv_file, 'a', newline='') as f:
			writer = csv.writer(f)
			if not file_exist:
				writer.writerow(self.headers)
			for item in data_list:
				row = self._generate_csv_line(item)
				try:
					writer.writerow(row)
				except:
					row[-1] = ''
					log('except: '+row[0])
					writer.writerow(row)

	def _generate_csv_line(self, item):
		row = []
		for col_name in self.headers:
			if col_name == 'tags':
				tags = ' '.join(item[col_name])
				row.append(tags)
			elif col_name == 'actor':
				actors = ' '.join(item[col_name])
				row.append(actors)
			else:
				row.append(item[col_name])
		return row

def main():
	log('Log--------------\n\n', True)
	spider = BangumiSpider()
	spider.run()


if __name__ == '__main__':
	main()