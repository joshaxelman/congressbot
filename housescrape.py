__author__ = 'jaxelman'
import sqlite3
import urllib2
from bs4 import BeautifulSoup

class HouseScrape:

	def __init__(self):
		self.db = sqlite3.connect('data/congress.db', isolation_level=None)
		self.get_zipcodes()
		#self.get_house_rep('90048')
		self.db.close()

	def get_zipcodes(self):
		cur = self.db.cursor()
		cur.execute('SELECT distinct(zip) FROM zipcodes where zip > 79789')
		zips = cur.fetchall()
		for zip in zips:
			self.get_house_rep(zip[0])

	def get_house_rep(self, zip):
		cur = self.db.cursor()
		url = "http://ziplook.house.gov/htbin/findrep?ZIP=" + zip
		page = urllib2.urlopen(url)
		soup = BeautifulSoup(page, "html.parser")
		for link in soup.find_all('a'):
			if 'house.gov' in link['href'] and 'm.house.gov' not in link['href']:
				name = link.get_text()
				if len(name) > 0:
					print ('Scraping ' + name + ' ' + zip)
					cur.execute("INSERT INTO house_rep (name, zip) VALUES (?, ?)", (name, zip))

HouseScrape()

