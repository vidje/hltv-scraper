"""
web scraper for hltv.org
by vid, 2023
"""
from datetime import datetime, timedelta
import requests as rq
import pandas as pd
from bs4 import BeautifulSoup

# fix error 403 for robots
HEADERS = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}

# create event urls
def get_event_urls(event_list):
	url = [f'https://www.hltv.org/results?event={e}' for e in event_list]
	return url

# get the necessary data from the web pages
def scrape_event_results(url):
	team1, team2, score, gdate_temp = [], [], [], []

	for u in url:
		r = rq.get(u, headers=HEADERS)
		soup = BeautifulSoup(r.content, 'html.parser')

		team1.extend([div.get_text().strip() for div in soup.find_all('div', class_='line-align team1')])
		score.extend([td.get_text().strip() for td in soup.find_all('td', class_='result-score')])
		team2.extend([div.get_text().strip() for div in soup.find_all('div', class_='line-align team2')])
		gdate_temp.extend([div.get('data-zonedgrouping-entry-unix') for div in soup.find_all('div', {'data-zonedgrouping-entry-unix': True})])

	return team1, team2, score, gdate_temp

# convert date to seconds, otherwise it's out of range
# calculate when was the last monday before game date
# since ranking pages get created only on mondays
def convert_date(gdate_temp):
	gdate = [(eval(i) / 1000) for i in gdate_temp]
	game_date, last_monday_date = [], []

	for i in gdate:
		game_date.append(datetime.fromtimestamp(i))

	for i in game_date:
		today = datetime.strptime(i.strftime('%Y-%m-%d'), '%Y-%m-%d')
		last_monday_date.append(today - timedelta(days=today.weekday()))

	return game_date, last_monday_date

def main():
	# get event ids from hltv.org/results
	# all big lans and their qualis of 2022 are listed below
	event_list = [
		6219, 6136, 6503, 6140, 6138,
        6381, 6382, 6379, 6380, 6372,
        6384, 6713, 6714, 6711, 6712,
        6588, 6586, 6137, 6141, 6343,
        6344, 6452, 6825, 6346, 6347,
        6349
	]

	url = get_event_urls(event_list)

	team1, team2, score, gdate_temp = scrape_event_results(url)

	# remove \n
	team1 = [i.strip() for i in team1]
	team2 = [i.strip() for i in team2]
	score = [i.strip() for i in score]

	game_date, last_monday_date = convert_date(gdate_temp)

	# use pandas to get data ready for export
	df = pd.DataFrame()
	df['team1'] = team1
	df['score'] = score
	df['team2'] = team2
	df['date_played'] = game_date
	df['last_rank_update_date'] = last_monday_date
	
	df[['team1_score', 'team2_score']] = df['score'].astype(str).str.split('-', expand=True).astype(int)
	df['date_played'] = df['date_played'].astype(str).str.split().str[0]
	df['last_rank_update_date'] = df['last_rank_update_date'].astype(str).str.split().str[0]
	df['last_rank_update_date'] = pd.to_datetime(df['last_rank_update_date'])
	df['last_rank_update_date'] = df['last_rank_update_date'].dt.strftime('%Y/%B/%d')
	df['last_rank_update_date'] = df['last_rank_update_date'].str.lower()
	df['last_rank_monday_url'] = 'https://www.hltv.org/ranking/teams/' + df['last_rank_update_date']
	
	df = df.reindex(columns=[
		'team1', 'team1_score', 'team2', 'team2_score',
		'last_rank_update_date', 'last_rank_monday_url'
		])
	df.to_excel('data.xlsx')

if __name__ == "__main__":
	main()

