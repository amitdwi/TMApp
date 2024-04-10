import json
import pymongo
import dns.resolver
dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers=['8.8.8.8']
url = "mongodb+srv://amitdwivedi:12345@cluster0.0zm9el6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = pymongo.MongoClient(url)
# database connection
db = pymongo.database.Database(client, 'slack_db')