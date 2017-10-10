from flask import Flask, render_template, flash, redirect, url_for
from flask import request
from bson.objectid import ObjectId
from bson.son import SON
from werkzeug.utils import secure_filename
import os, time, datetime
# from flask_pymongo import PyMongo
from pymongo import MongoClient

UPLOAD_FOLDER = './static/images/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = 'Ca$ablanca'

# mongo = PyMongo(app)
client = MongoClient("localhost", 27017)
db = client.tejia

@app.route('/')
def home():
	pipeline = [
		{ "$group": {"_id": "$name", "branchs": {"$push": "$address"}, "count": {"$sum": 1}}}
	]
	gp = list(db.markets.aggregate(pipeline))
	print(gp)
	# result = []
	# markets = db.markets.find()
	# for market in markets:
	# 	result.append({"id":market["_id"], "name":market["name"], "address":market["address"]})
	return render_template('index.html', markets=gp)

@app.route('/add', methods=['POST', 'GET'])
def add_product():
	if request.method == 'POST':
		# print(request.form['name'],request.form['address'])
		post_id = db.markets.insert_one({'name':request.form['name'],'branch': request.form['branch'], 'address':request.form['address']}).inserted_id
		flash('new makret added')
		error = None
		return redirect(url_for('add_product'))
	else:
		error = 'Invalid username/password'
	return render_template('add_product.html', error=error)

@app.route('/delete', methods=['POST'])
def delete_product():
	if request.method == 'POST':
		_id = (request.form['marketId'])
		result = db.markets.delete_one({'_id': ObjectId(_id)})
		flash(str(result) + ' makret deleted')
		error = None
		return redirect(url_for('home'))
	else:
		error = 'makret not exist'
	return  redirect(url_for('home'))

@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		f = request.files['file']
		filename_ext = secure_filename(f.filename).split('.')[-1]
		print(filename_ext)
		current_milli_time = lambda: int(round(time.time() * 1000))
		img_name = str(current_milli_time())[4:] + '.' + filename_ext
		f.save(os.path.join(app.config['UPLOAD_FOLDER'], img_name))
		db.products.insert_one({'img': img_name, "last_modified": datetime.datetime.now()})
		return render_template('index.html')

	# else:
	# 	return redirect(url_for('home'));

@app.route('/products', methods=['POST', 'GET'])
def products():
	results = []
	products = db.products.find()
	for product in products:
		results.append({"id":product["_id"], "img":product["img"]})
	print(results)
	return render_template('products.html', products=results)
if __name__ == '__main__':
	app.run(debug=True)