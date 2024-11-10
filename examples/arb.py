import time
from rtg import *

def sell_highest(s, i, fruit):
	if i[fruit] > 0:
		best = ""
		best_price = 0
		for venue in ("zurich", "london", "frankfurt"):
			if s[venue][fruit].bid.price > best_price:
				best_price = s[venue][fruit].bid.price
				best = venue
		sell(venue, fruit, 0, i[fruit])

def check_arb(s, fruit, v1, v2):
	if s[v1][fruit].ask.price < s[v2][fruit].bid.price:
		qty = min(s[v1][fruit].ask.qty, s[v2][fruit].ask.qty)

		if qty > 0:
			q1 = buy(v1, fruit, s[v1][fruit].ask.price, qty)
			q2 = sell(v2, fruit, s[v1][fruit].ask.price, qty)
			s[v1][fruit].ask.qty -= qty
			s[v2][fruit].bid.qty -= qty
			print(fruit, v1, s[v1][fruit].ask.price, v2, s[v2][fruit].bid.price, qty, q1, q2)

		return qty
	return 0

login("abc", "abc")

while True:
	s, i = get()
	total = 0
	for fruit in ("apples", "bananas", "tomatoes"):
		sell_highest(s, i, fruit)
		total += check_arb(s, fruit, "zurich", "london")
		total += check_arb(s, fruit, "london", "zurich")
		total += check_arb(s, fruit, "zurich", "frankfurt")
		total += check_arb(s, fruit, "frankfurt", "zurich")
		total += check_arb(s, fruit, "london", "frankfurt")
		total += check_arb(s, fruit, "frankfurt", "london")
	if total == 0:
		time.sleep(1)

