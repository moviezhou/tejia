from flask import Flask, render_template, flash, redirect, url_for
from flask import request
from bson.objectid import ObjectId
# from flask_pymongo import PyMongo
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'Ca$ablanca'

# mongo = PyMongo(app)
client = MongoClient("localhost", 27017)
db = client.tejia

@app.route('/')
def home():
	result = []
	markets = db.markets.find()
	for market in markets:
		result.append({"id":market["_id"], "name":market["name"], "address":market["address"]})
	return render_template('index.html', markets=result)

@app.route('/add', methods=['POST', 'GET'])
def add_product():
	if request.method == 'POST':
		# print(request.form['name'],request.form['address'])
		post_id = db.markets.insert_one({'name':request.form['name'], 'address':request.form['address']}).inserted_id
		flash('new makret added')
		error = None
		return redirect(url_for('add_product'))
	else:
		error = 'Invalid username/password'
	return render_template('add_product.html', error=error)

@app.route('/delete', methods=['POST'])
def delete_product():
	if request.method == 'POST':
		_id = (request.form['selectId'])
		result = db.markets.delete_one({'_id': ObjectId(_id)})
		flash(str(result) + ' makret deleted')
		error = None
		return redirect(url_for('home'))
	else:
		error = 'makret not exist'
	return  redirect(url_for('home'))

if __name__ == '__main__':
	app.run(debug=True)