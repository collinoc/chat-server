from flask import Flask, render_template, url_for, request, redirect, session, flash, abort
from flask_sqlalchemy import SQLAlchemy

# INIT #

app = Flask(__name__)
app.secret_key = b'<\x1a\xd1\xef1\xc6U\xfa\xf2\xf6\xfe\xda!W\xca%'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
db = SQLAlchemy(app)

# DB #

class ChatRoom (db.Model):
	__tablename__ = "chatroom"
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(20), unique=True)
	owner = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __init__(self, name):
		self.name = name
		self.owner = int(session["uid"])

class User (db.Model):
	__tablename__ = "user"
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), unique=True)
	password = db.Column(db.String(80))

	def __init__(self, username, password):
		self.username = username
		self.password = password

class Message (db.Model):
	__tablename__ = "message"
	id = db.Column(db.Integer, primary_key=True)
	sender = db.Column(db.Integer, db.ForeignKey('user.id'))
	content = db.Column(db.String(256))
	chat = db.Column(db.Integer, db.ForeignKey('chatroom.id'))

	def __init__(self, sender, content):
		self.sender = sender
		self.content = content
		self.chat = int(session["chat_id"])

# FLASK #

@app.cli.command("initdb")
def init_database():
	print("Initializing database...", end=" ")
	db.drop_all()
	db.create_all()

	# db.session.add( User("user", "123") )

	db.session.commit()
	print("Complete.")

@app.route("/")
def index():
	if "username" in session:
		return redirect( url_for("chatrooms") )
	return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
	try:
		query = User.query.filter_by(username=request.form["username"]).one()
	except:
		flash("Username does not exist!")
		return redirect( url_for("index") )

	if not query or not query.password == request.form["password"]:		
			flash("Incorrect password!")
			return redirect( url_for("index") )
	else:
		session["username"] = query.username
		session["password"] = query.password
		session["uid"] = query.id

	return redirect( url_for("chatrooms") )

@app.route("/create-account", methods=["GET", "POST"])
def create_account():
	if request.method == "POST":
		if request.form["password"] != request.form["confirm_password"]:
			flash("Passwords don't match!")
			return render_template("create_account.html")
		else:
			try:
				new_user = User(
					request.form["username"], 
					request.form["password"]
				)
				db.session.add( new_user )
				db.session.commit()
			except:
				flash("Username already taken!")
				return redirect( url_for('create_account') )

			session["username"] = request.form["username"]
			session["password"] = request.form["password"]
			session["uid"] = new_user.id

			return redirect( url_for("chatrooms") )
	else: # GET
		return render_template("create_account.html")

@app.route("/logout")
def logout():
	session.clear()
	return redirect( url_for("index") )

@app.route("/chatrooms")
def chatrooms():	
	if not "username" in session:
		return redirect( url_for("index") )
	return render_template("chatrooms.html")

@app.route("/create_room", methods=["GET", "POST"])
def create_room():
	if request.method == "POST":
		try:
			newRoom = ChatRoom(request.form["room-name"])
			db.session.add( newRoom )
			db.session.commit()
			return redirect( url_for("join_room", room=newRoom.id, name=newRoom.name) )
		except:
			flash("A room with that name already exists!")
			return redirect( url_for("create_room") )
	else: # GET
		return render_template("create_room.html")

@app.route("/join/id=<room>name=<name>")
def join_room(room, name):
	if "chatroom" in session and name != session["chatroom"]:
		flash("You're already in another chat room! You must leave your old one first!")
		return redirect( url_for("index") )
	session["chatroom"] = name
	session["chat_id"] = room
	return redirect( url_for("chat", room=room) )

@app.route("/chat/<room>")
def chat(room):
	return render_template("chat.html")

@app.route("/leave")
def leave_room():
	if "chatroom" in session:
		del session["chatroom"]
		del session["chat_id"]
	return redirect( url_for('index') )

@app.route("/get_chats", methods=["GET"])
def chats_list():
	query = ChatRoom.query.all()
	return  {
		"rooms": [{ 
			"id": room.id, 
			"name": room.name, 
			"owner": room.owner
		} for room in query]
	}

@app.route("/delete_chat/<room>", methods=["DELETE"])
def delete_chat(room):
	try:
		ChatRoom.query.filter_by(id=room).delete()
		Message.query.filter_by(chat=room).delete()
		db.session.commit()
	except:
		flash("There was no room to delete!")
	return "OK", 204

@app.route("/get_messages", methods=["GET"])
def get_messages():
	query = Message.query.filter_by(chat=session["chat_id"]).all()
	session["received"] = []

	response = {
		"messages": [{ 
			"sender": message.sender, 
			"content": message.content 
		} for message in query]
	}
	
	new_received = session["received"].copy()
	for message in query:
		new_received.append(message.id)

	session["received"] = new_received

	return response

@app.route("/get_new_messages", methods=["GET"])
def get_new_messages():
	response = { "messages": [] }
	new_received = []
	try:
		query = Message.query.filter_by(chat=session["chat_id"]).all()

		response = {
			"messages": [{ 
				"sender": message.sender, 
				"content": message.content 
			} for message in query if not message.id in session["received"]]
		}

		new_received = session["received"].copy()
		for message in query:
			if not message.id in session["received"]:
				new_received.append(message.id)
	except:
		print("Error getting messages. Chatroom was likely deleted.")

	session["received"] = new_received

	return response

@app.route("/send_message", methods=["POST"])
def send_message():
	if not ChatRoom.query.filter_by(id=session["chat_id"]).first():
		del session["chatroom"]
		del session["chat_id"]
		return redirect( url_for("chatrooms") )
	db.session.add( Message(session["username"], request.json["message"]) )
	db.session.commit()
	return request.json["message"]

@app.route("/get_user")
def get_user():
	return { "username": session["username"], "uid": session["uid"] }

if __name__ == "__main__":
	app.run(
		host="localhost", 
		port=5000
	)

	