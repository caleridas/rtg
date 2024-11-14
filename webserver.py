#!/usr/bin/python3

import http.server
import socketserver
import urllib.parse
import os
from typing import Union, Dict
import dataclasses
import json
import numpy
import threading
import time
import math

@dataclasses.dataclass
class UserInfo:
	name : str
	pw : str
	cash : int = 10000
	inventory : Dict[str,int] = dataclasses.field(
		default_factory=lambda: {
			"apples": 0,
			"bananas": 0,
			"tomatoes": 0
		}
	)

	@staticmethod
	def from_dict(d):
		return UserInfo(
			name=d["name"],
			pw=d["pw"],
			cash=d["cash"],
			inventory={
				"apples": d["inventory"]["apples"],
				"bananas": d["inventory"]["bananas"],
				"tomatoes": d["inventory"]["tomatoes"]
			}
		)
	def to_dict(self):
		return {
			"name": self.name,
			"pw": self.pw,
			"cash": self.cash,
			"inventory": self.inventory.copy()
		}

@dataclasses.dataclass
class SideInfo:
	price : int = 100
	qty : int = 10

	@staticmethod
	def from_dict(d):
		return SideInfo(**d)

	def to_dict(self):
		return self.__dict__

@dataclasses.dataclass
class FruitInfo:
	name : str
	ask : SideInfo = dataclasses.field(default_factory=SideInfo)
	bid : SideInfo = dataclasses.field(default_factory=SideInfo)

	@staticmethod
	def from_dict(d):
		return FruitInfo(
			name=d["name"],
			ask=SideInfo.from_dict(d["ask"]),
			bid=SideInfo.from_dict(d["bid"])
		)

	def to_dict(self):
		return {
			"name": self.name,
			"ask": self.ask.to_dict(),
			"bid": self.bid.to_dict()
		}

@dataclasses.dataclass
class VenueInfo:
	name : str
	fruits : Dict[str, FruitInfo] = dataclasses.field(
		default_factory=lambda: {
			"apples": FruitInfo(name="apples"),
			"bananas": FruitInfo(name="bananas"),
			"tomatoes": FruitInfo(name="tomatoes")
		}
	)
	@staticmethod
	def from_dict(d):
		return VenueInfo(
			name=d["name"],
			fruits={
				"apples": FruitInfo.from_dict(d["fruits"]["apples"]),
				"bananas": FruitInfo.from_dict(d["fruits"]["bananas"]),
				"tomatoes": FruitInfo.from_dict(d["fruits"]["tomatoes"])
			}
		)

	def to_dict(self):
		return {
			"name": self.name,
			"fruits": {
				"apples": self.fruits["apples"].to_dict(),
				"bananas": self.fruits["bananas"].to_dict(),
				"tomatoes": self.fruits["tomatoes"].to_dict()
			}
		}

@dataclasses.dataclass
class State:
	users : Dict[str, UserInfo] = dataclasses.field(default_factory=dict)
	venues : Dict[str, VenueInfo] = dataclasses.field(
		default_factory=lambda: {
			"zurich": VenueInfo(name="zurich"),
			"frankfurt": VenueInfo(name="frankfurt"),
			"london": VenueInfo(name="london")
		}
	)
	time: float = 0.0

	@staticmethod
	def from_dict(d):
		return State(
			users={u["name"] : UserInfo.from_dict(u) for u in d["users"]},
			venues = {
				"zurich": VenueInfo.from_dict(d["venues"]["zurich"]),
				"frankfurt": VenueInfo.from_dict(d["venues"]["frankfurt"]),
				"london": VenueInfo.from_dict(d["venues"]["london"]),
			}
		)

	def to_dict(self):
		return {
			"users": [u.to_dict() for u in self.users.values()],
			"venues": {
				"zurich": self.venues["zurich"].to_dict(),
				"frankfurt": self.venues["zurich"].to_dict(),
				"london": self.venues["london"].to_dict()
			}
		}

def init_qty():
	return 5 + numpy.random.poisson(3)

def price_increment():
	return numpy.random.gamma(1, 2)

def save_state():
	global state_lock
	global state
	with state_lock:
		open("state.json", "w").write(json.dumps(state.to_dict()))

state_lock = threading.Lock()
state = State()

try:
	js = json.loads(open("state.json", "r").read())
	state = State.from_dict(js)
except:
	pass

# XXX: implement save and restore so this can be restarted without erasing
# accounts

def get_auth_user(username, password):
	user = state.users.get(username)
	print(user)
	if user and user.pw == password:
		return user
	else:
		return None

def read_asset(name : str, mode : str = "rb") -> Union[str, bytes]:
	with open(os.path.join("assets", name), mode) as f:
		return f.read()

def handle_root(query : Dict[str, str]):
	with state_lock:
		user = get_auth_user(query.get("u"), query.get("p"))
		if user:
			return handle_mainview(user)
		else:
			return handle_loginview()

LOGIN = read_asset("login.html", "r")
def handle_loginview():
	return (200, "text/html", LOGIN)

MAIN = read_asset("main.html", "r")
def handle_mainview(user):
	return (200, "text/html", MAIN.replace("$USER", user.name).replace("$PASSWORD", user.pw))

VIEW = read_asset("view.html", "r")
def handle_view(query):
	return (200, "text/html", VIEW)

INSTRUCTIONS = read_asset("python_instruction.html", "r")
def handle_instructions(query):
	return (200, "text/html", INSTRUCTIONS)


REGISTER_SUCCESS = read_asset("register_success.html", "r")
REGISTER_FAILED = read_asset("register_failed.html", "r")
def handle_register(query : Dict[str, str]):
	result = (200, "text/html", REGISTER_FAILED)
	with state_lock:
		if "u" in query and "p1" in query and "p2" in query and query["u"] not in state.users and query["p1"] == query["p2"]:
			user = UserInfo(name=query["u"], pw=query["p1"])
			state.users[query["u"]] = user
			result = (200, "text/html", REGISTER_SUCCESS)
	save_state()
	return result

def handle_trade(query : Dict[str, str]):
	with state_lock:
		user = get_auth_user(query.get("u"), query.get("p"))
		if user:
			amount = 0
			price = int(query["price"])
			qty = int(query["qty"])
			fruit_name = query["fruit"]
			venue = state.venues[query["venue"]]
			fruit = venue.fruits[fruit_name]
			if query["dir"] == "buy":
				while qty and int(fruit.ask.price) <= price and user.cash > int(fruit.ask.price):
					q = min(fruit.ask.qty, qty, user.cash // int(fruit.ask.price))
					fruit.ask.qty -= q
					user.inventory[fruit_name] += q
					user.cash -= q * int(fruit.ask.price)
					amount += q
					qty -= q
					if fruit.ask.qty == 0:
						fruit.ask.qty = init_qty()
						fruit.ask.price += price_increment()
			if query["dir"] == "sell":
				while qty and int(fruit.bid.price) >= price and user.inventory[fruit_name] > 0:
					q = min(fruit.bid.qty, qty, user.inventory[fruit_name])
					fruit.bid.qty -= q
					user.inventory[fruit_name] -= q
					user.cash += q * int(fruit.bid.price)
					amount += q
					qty -= q
					if fruit.bid.qty == 0:
						fruit.bid.qty = init_qty()
						fruit.bid.price -= price_increment()
			return (200, "text/html", str(amount) + "\n")
		else:
			return (400, "text/plain", "forbidden")

def handle_state(query : Dict[str, str]):
	with state_lock:
		user = get_auth_user(query.get("u"), query.get("p"))
		if user:
			s_dict = {}
			for venue_name, venue in state.venues.items():
				for fruit_name, fruit in venue.fruits.items():
					for side_name, side in (("ask", fruit.ask), ("bid", fruit.bid)):
						s_dict[venue_name + "." + fruit_name + "." + side_name + ".price"] = int(side.price)
						s_dict[venue_name + "." + fruit_name + "." + side_name + ".qty"] = int(side.qty)

			for fruit_name, qty in user.inventory.items():
				s_dict["inventory." + fruit_name] = qty
			s_dict["inventory.cash"] = user.cash

			return (200, "application/json", json.dumps(s_dict))
		else:
			return (400, "text/plain", "forbidden")

def handle_marketstate(query : Dict[str, str]):
	with state_lock:
		s_dict = {}
		for venue_name, venue in state.venues.items():
			for fruit_name, fruit in venue.fruits.items():
				for side_name, side in (("ask", fruit.ask), ("bid", fruit.bid)):
					s_dict[venue_name + "." + fruit_name + "." + side_name + ".price"] = int(side.price)
					s_dict[venue_name + "." + fruit_name + "." + side_name + ".qty"] = int(side.qty)

		return (200, "application/json", json.dumps(s_dict))

def image_handler(filename, mime_type="image/jpeg"):
	IMAGE = read_asset(filename, "rb")
	def handle_image(query):
		return (200, mime_type, IMAGE)
	return handle_image

handler_map = {
	"/": handle_root,
	"/register": handle_register,
	"/trade": handle_trade,
	"/state": handle_state,
	"/marketstate": handle_marketstate,
	"/view": handle_view,
	"/zurich.jpg": image_handler("zurich.jpg"),
	"/frankfurt.jpg": image_handler("frankfurt.jpg"),
	"/london.jpg": image_handler("london.jpg"),
	"/instructions": handle_instructions
}

def update_state(state):
	attractors = {
		"apples" : 100 + 20 * math.sin(0.1 * state.time),
		"bananas" : 120 - 20 * math.cos(0.05 * state.time),
		"tomatoes" : 100 - 30 * math.sin(0.025 * state.time)
	}

	state.time += 1

	for fruit in ("apples", "bananas", "tomatoes"):
		total = attractors[fruit] * 5
		count = 5
		for venue in ("zurich", "frankfurt", "london"):
			total += state.venues[venue].fruits[fruit].ask.price + state.venues[venue].fruits[fruit].bid.price
			count += 2
		avg = total / count
		for venue in ("zurich", "frankfurt", "london"):
			point = state.venues[venue].fruits[fruit]
			point.ask.price -= price_increment()
			point.bid.price += price_increment()

			point.ask.price = 0.95 * point.ask.price + 0.05 * avg
			point.bid.price = 0.95 * point.bid.price + 0.05 * avg

			while point.ask.price < point.bid.price + 2:
				point.ask.price += 2
				point.ask.qty = init_qty()
				point.bid.price -= 2
				point.bid.qty = init_qty()

def thread_function():
	save_counter = 30
	while not thread_exit:
		time.sleep(2)
		with state_lock:
			update_state(state)
		if save_counter == 0:
			save_state()
			save_counter = 30
		save_counter = save_counter - 1

thread_exit = False
thread = threading.Thread(target=thread_function)
thread.start()

class Handler(http.server.BaseHTTPRequestHandler):
	def do_GET(self):
		url = urllib.parse.urlparse(self.path, scheme="http")
		path = url.path
		query = dict(urllib.parse.parse_qsl(url.query))

		self.invoke_handler(handler_map.get(path), query)

	def do_POST(self):
		content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
		post_data = self.rfile.read(content_length) # <--- Gets the data itself

		url = urllib.parse.urlparse(self.path, scheme="http")
		path = url.path
		query = { x.decode("utf-8") : y.decode("utf-8") for x,y in urllib.parse.parse_qsl(post_data) }

		self.invoke_handler(handler_map.get(path), query)

	def invoke_handler(self, handler, query):
		if handler:
			code, content_type, content = handler(query)
			self.send_response(code)
			self.send_header("Content-Type", content_type)
			self.end_headers()
			self.wfile.write(content.encode("utf-8") if isinstance(content, str) else content)
		else:
			self.send_error(400, "Not found")

class TCPServer(socketserver.TCPServer):
	allow_reuse_address = True

try:
	with TCPServer(("", 8080), Handler) as httpd:
		httpd.serve_forever()
finally:
	with state_lock:
		thread_exit = True
	thread.join()
	save_state()
