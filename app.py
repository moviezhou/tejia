from flask import Flask, render_template, flash, redirect, url_for
from flask import request
from bson.objectid import ObjectId
from bson.son import SON
from werkzeug.utils import secure_filename
from datetime import datetime
import os, time
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
	# { "$group": {"_id": "$name", "branchs": {"$push": "$address"}, "count": {"$sum": 1}}}
	pipeline = [
		{ "$group": {"_id": "$name", "branchs": {"$push": {"id": "$_id","branch": "$branch", "address": "$address"}}, "count": {"$sum": 1}}}
		# { "$group": {"_id": "$name", "branchs": {"$push": {"branch": "$address"}, "count": {"$sum": 1}}}}
		]
	gp = list(db.markets.aggregate(pipeline))
	# result = []
	# markets = db.markets.find()
	# for market in markets:
	# 	result.append({"id":market["_id"], "name":market["name"], "address":market["address"]})
	return render_template('index.html', markets=gp)

@app.route('/addmarket', methods=['POST', 'GET'])
def add_market():
	if request.method == 'POST':
		# print(request.form['name'],request.form['address'])
		coordinates = list(map((lambda x:float(x)),request.form['location'].split(',')))
		
		#location: {type: "Point", coordinates: [103.731937,36.104303]}, branch: "西太华科教城店",address:"安宁区宝石花路",name: "西太华超市"
		post_id = db.markets.insert_one({'location':{'type': 'Point', 'coordinates': coordinates },'branch': request.form['branch'], 
			'contact': request.form['contact'], 'phone': request.form['phone'], 'address':request.form['address'], 'name': request.form['name']})
		flash('new makret added')
		error = None
		return redirect(url_for('add_market'))
	else:
		error = 'Invalid username/password'
	return render_template('add_market.html', error=error)

@app.route('/updatemarket/<marketid>', methods=['POST', 'GET'])
def update_market(marketid):
	if(marketid):
		if request.method == 'GET':
			market = db.markets.find_one({'_id': ObjectId(marketid)})
			return render_template('update_market.html', market = market)
		elif request.method == 'POST':
			db.markets.update_one(
				{'_id': ObjectId(marketid)},{
				'$set': {
				'name': request.form['name'],
				'branch': request.form['branch'],
				'contcat': request.form['contact'],
				'phone': request.form['phone'],
				'address': request.form['address'],
				'location': {'type': 'Point', 'coordinates': request.form['location']}
				}
				})
			flash('Market updated')
			return redirect(url_for('update_market', marketid = marketid))
	else:
		flash('marketid is null')
		redirect(url_for('home'))


@app.route('/delete', methods=['POST'])
def delete_product():
	if request.method == 'POST':
		_id = (request.form['marketId'])
		result = db.markets.delete_one({'_id': ObjectId(_id)})
		flash(_id + ' market deleted')
		error = None
		return redirect(url_for('home'))
	else:
		error = 'market not exist'
	return  redirect(url_for('home'))

@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		f = request.files['file']
		filename_ext = secure_filename(f.filename).split('.')[-1]
		current_milli_time = lambda: int(round(time.time() * 1000))
		img_name = str(current_milli_time())[4:] + '.' + filename_ext
		f.save(os.path.join(app.config['UPLOAD_FOLDER'], img_name))
		db.products.insert_one({'market_id': ObjectId(request.form['marketId']), 'img': img_name, "last_modified": datetime.utcnow()})
		return redirect(url_for('add_products', marketid=request.form['marketId']))

	# else:
	# 	return redirect(url_for('home'));

@app.route('/addproduct/<marketid>', methods=['POST', 'GET'])
def add_products(marketid):
	results = []
	market = db.markets.find_one({'_id': ObjectId(marketid)})
	products = db.products.find({'market_id': ObjectId(marketid)});
	branch = market['name'] + market['branch']
	for product in products:
		results.append({'id': product['market_id'], 'img': product['img']})
	return render_template('add_product.html',marketid = marketid , branch= branch, products=results)


@app.route('/products', methods=['POST', 'GET'])
def products():
	results = []
	# pipeline = [
	# 	{ "$lookup": 
	# 		{
	# 		"from": "markets",
 #          	"localField": "market_id",
 #          	"foreignField": "_id",
 #          	"as": "branch"
 #          }}
	# 	# { "$group": {"_id": "$name", "branchs": {"$push": {"branch": "$address"}, "count": {"$sum": 1}}}}
	# 	]
	# products = list(db.products.aggregate(pipeline))
	# 
	products = db.products.find();
	for product in products:
		results.append({'id': product['market_id'], 'img': product['img']})
	return render_template('products.html', products=results)

if __name__ == '__main__':
	app.run(host= '0.0.0.0', debug=True)