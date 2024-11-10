import time
from rtg import *
import csv

login("abc", "abc")

f = open("stats.csv", "w")

cf = csv.writer(f)

while True:
	s, i = get()
	cf.writerow((
		s["zurich"]["apples"].bid.price,
		s["zurich"]["apples"].ask.price,
		s["frankfurt"]["apples"].bid.price,
		s["frankfurt"]["apples"].ask.price,
		s["london"]["apples"].bid.price,
		s["london"]["apples"].ask.price
	))
	f.flush()
	time.sleep(1)
