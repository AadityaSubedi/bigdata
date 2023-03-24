# Import necessary libraries
from elasticsearch import Elasticsearch
from flask import Flask, redirect, render_template, request
from pymongo import MongoClient
from json import loads
from bson.json_util import dumps
from bson.objectid import ObjectId
# Create a Flask app
app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["todo_db"]
collection = db["todo_collection"]

# Connect to ElasticSearch
# es = Elasticsearch()
# create an Elasticsearch object
es = Elasticsearch(
    hosts=["http://localhost:9200"], # specify the host and port of your Elasticsearch instance
    basic_auth=('arpanuu', 'gyawali'), # provide your username and password for authentication
)

# Define a route to add a new todo
@app.route('/', methods=['GET', 'POST'])
def home():
    # Render the add todo form template
    return render_template('home.html')

# Define a route to add a new todo
@app.route('/add_todo', methods=['GET', 'POST'])
def add_todo():
    if request.method == 'POST':
        # Get the todo details from the user
        title = request.form['title']
        time_allocated = request.form['time_allocated']
        tags = request.form['tags']
        day = request.form['day']

        # Insert the todo into MongoDB
        todo = {"title": title, "time_allocated": time_allocated, "tags": tags, "day": day}
        collection.insert_one(todo)
        todo_id = todo["_id"]
        del todo["_id"]
        todo =loads(dumps(todo))
        
        
        # Index the todo in ElasticSearch
        es.index(index="todos", body=todo, id = todo_id)

        # Redirect to the home page
        # return redirect('/add_todo')
        return redirect('/')

    # Render the add todo form template
    return render_template('add_todo_form.html')

# Define a route to search for todos
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        # Get the search query from the user
        query = request.form['query']
        tag = request.form['search_type']

        # Search for the query in ElasticSearch
        if (tag == 'day'):
            results = es.search(index="todos", body={"query": {"match": {"day": query}}})
        else:
            results = es.search(index="todos", body={"query": {"match": {"tags": query}}})
        print(results)

        # Get the ids of the matching todos
        ids = [ObjectId(hit['_id']) for hit in results['hits']['hits']]
        print(ids)

        # Get the matching todos from MongoDB
        todos = collection.find({"_id": {"$in": ids}})
        todos = loads(dumps(todos))

        # Render the search results template
        return render_template('home.html', todos=todos, search = True)

    # Render the search form template
    return render_template('search_form.html')

if __name__ == '__main__':
    app.run(debug=True)
