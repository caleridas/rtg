#!/usr/bin/python3

import dataclasses
import json
import urllib.request

@dataclasses.dataclass
class Side:
	price : int
	qty : int

	@staticmethod
	def from_dict(d, prefix):
		return Side(price=int(d[prefix + ".price"]), qty=int(d[prefix + ".qty"]))

	def __getitem__(self, key):
		return getattr(self, key)

@dataclasses.dataclass
class Fruit:
	ask : Side
	bid : Side

	@staticmethod
	def from_dict(d, prefix):
		return Fruit(
			ask=Side.from_dict(d, prefix + ".ask"),
			bid=Side.from_dict(d, prefix + ".bid")
		)

	def __getitem__(self, key):
		return getattr(self, key)


@dataclasses.dataclass
class Venue:
	apples : Fruit
	bananas : Fruit
	tomatoes : Fruit

	@staticmethod
	def from_dict(d, prefix):
		return Venue(
			apples = Fruit.from_dict(d, prefix + ".apples"),
			bananas = Fruit.from_dict(d, prefix + ".bananas"),
			tomatoes = Fruit.from_dict(d, prefix + ".tomatoes")
		)

	def __getitem__(self, key):
		return getattr(self, key)

@dataclasses.dataclass
class Inventory:
	cash : int
	apples : int
	bananas : int
	tomatoes : int

	@staticmethod
	def from_dict(d, prefix):
		return Inventory(
			cash=int(d[prefix + ".cash"]),
			apples=int(d[prefix + ".apples"]),
			bananas=int(d[prefix + ".bananas"]),
			tomatoes=int(d[prefix + ".tomatoes"]),
		)

	def __getitem__(self, item):
		return getattr(self, item)

@dataclasses.dataclass
class State:
	zurich : Venue
	frankfurt : Venue
	london : Venue

	@staticmethod
	def from_dict(d):
		return State(
			zurich=Venue.from_dict(d, "zurich"),
			frankfurt=Venue.from_dict(d, "frankfurt"),
			london=Venue.from_dict(d, "london")
		)

	def __getitem__(self, item):
		return getattr(self, item)

_host = None
_username = None
_password = None

def login(username="abc", password="abc", host="http://localhost:8080"):
	global _host
	global _username
	global _password
	_host = host
	_username = username
	_password = password

def get():
	reply = urllib.request.urlopen(
		_host + "/state?" + urllib.parse.urlencode(
			{
				"u": _username,
				"p": _password,
			}
		)
	)
	data = reply.read()
	js = json.loads(data)
	return (State.from_dict(js), Inventory.from_dict(js, "inventory"))

def trade(venue : str, fruit : str, price : int, qty : int, dir : str):
	reply = urllib.request.urlopen(
		_host + "/trade?" + urllib.parse.urlencode(
			{
				"u": _username,
				"p": _password,
				"venue": venue,
				"fruit": fruit,
				"price": price,
				"qty": qty,
				"dir": dir
			}
		)
	)
	data = reply.read()
	return int(data)

def buy(venue : str, fruit : str, price : int, qty : int):
	return trade(venue, fruit, price, qty, "buy")

def sell(venue : str, fruit : str, price : int, qty : int):
	return trade(venue, fruit, price, qty, "sell")
