from flask import Flask, render_template, flash, redirect, url_for
from flask import request
from flask import jsonify
from flask import Flask, request, make_response
from flask_restful import Resource, Api
import json
from bson.objectid import ObjectId
from bson.son import SON
from bson import json_util
from werkzeug.utils import secure_filename
from datetime import datetime
import os, time
# from flask_pymongo import PyMongo
from pymongo import MongoClient

UPLOAD_FOLDER = './static/images/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


app = Flask(__name__)
api = Api(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.update(RESTFUL_JSON=dict(ensure_ascii=False))

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
def delete_market():
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
		# Convert js utc date format to python datetime object
		start_date = datetime.strptime(request.form['startdate'], "%a, %d %b %Y %H:%M:%S %Z")
		end_date = datetime.strptime(request.form['startdate'], "%a, %d %b %Y %H:%M:%S %Z")

		f = request.files['file']
		filename_ext = secure_filename(f.filename).split('.')[-1]
		current_milli_time = lambda: int(round(time.time() * 1000))
		img_name = str(current_milli_time())[4:] + '.' + filename_ext
		f.save(os.path.join(app.config['UPLOAD_FOLDER'], img_name))

		db.products.insert_one({'market_id': ObjectId(request.form['marketId']), 'img': img_name, 
			'start_date': start_date, 'end_date': end_date, 'last_modified': datetime.utcnow()})
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
		results.append({'marketid': product['market_id'],'id': product['_id'], 'img': product['img']})
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

@app.route('/product/delete', methods=['POST'])
def delete_product():
	if request.method == 'POST':
		# print('AAA',request.get_data().decode('utf-8'))
		
		# get post requrst json data
		# With silent=True set, the get_json function will fail silently
		data = request.get_json(silent=True)
		productId = data['productId']
		if productId:
			product = db.products.find_one({'_id': ObjectId(productId)})
			if product:
				file = os.path.join(app.config['UPLOAD_FOLDER'], product['img'])
				if os.path.isfile(file):
					os.remove(file)
					db.products.remove({'_id': ObjectId(productId)})
					return jsonify({'data': 'success'})
		return jsonify({'data':'failed'})



# Restful API
class HelloWorld(Resource):
    def get(self):
    	results = []
    	pipeline = [
    	{"$lookup":{"from": "markets", "localField": "market_id", "foreignField": "_id", "as": "market"}},
    	{ 
        "$project" : {
        	"img": 1, 
            "market.name" : 1, 
            "market.branch" : 1,
            "market.location.coordinates" : 1 
        }}
    	]
    	products = list(db.products.aggregate(pipeline))
    	print(products)
    	for product in products:
    		results.append({'img': product['img']})
    	return [json.loads(json.dumps(item, indent=4, default=json_util.default))
                for item in products]
    	#return products 

api.add_resource(HelloWorld, '/test')


if __name__ == '__main__':
	app.run(host= '0.0.0.0', debug=True)