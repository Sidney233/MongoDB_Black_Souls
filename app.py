from flask import render_template, flash, redirect, url_for, Flask, request, session
from flask_apscheduler import APScheduler
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import random
import bisect
from apscheduler.schedulers.background import BackgroundScheduler


class Config(object):
    SECRET_KEY = "you - will - never - guess"
    MONGO_URI = "mongodb://localhost:27017/black_souls"


app = Flask(__name__)
app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
mongo = PyMongo(app)
career = {'knight':
              {'weapon_name': '长剑',
               'weapon_attack': 1,
               'armors': [{'armor_name': '骑士头盔', 'armor_defense': 1}, {'armor_name': '骑士铠甲', 'armor_defense': 3}]
               },
          'warrior':
              {'weapon_name': '战斧',
               'weapon_attack': 2,
               'armors': [{'armor_name': '佣兵头盔', 'armor_defense': 1}, {'armor_name': '佣兵铠甲', 'armor_defense': 2}]
               }
          }
rare_list = [1, 2, 3, 4, 5]
scheduler = BackgroundScheduler()
scheduler.start()
users_dic = {}
MAX_ITEM = 5


@scheduler.scheduled_job('interval', seconds=10)
def flag():
    global users_dic
    for key in users_dic:
        users_dic[key] = 1
    print("reset")


def weight_choice(weight):
    weight_sum = []
    sum = 0
    for a in weight:
        sum += a
        weight_sum.append(sum)
    t = random.randint(0, sum - 1)
    return bisect.bisect_right(weight_sum, t)


def weight_count(luck):
    weight = []
    for i in range(5):
        if luck >= 10:
            luck = luck - 10
            weight.append(10)
        elif 0 < luck < 10:
            weight.append(luck)
            luck = 0
        else:
            weight.append(luck)
    return weight


def is_full(username):
    find_user = mongo.db.users.find_one({"username": username})
    user = User(id=find_user['_id'], username=find_user['username'],
                password_hash=find_user["password_hash"], armor_ids=find_user["armor_ids"],
                weapon_id=find_user["weapon_id"], items_ids=find_user['items_ids'], gold=find_user['gold'])
    min = {"_id": "0", "value": 100000}
    if len(user.items_ids) >= MAX_ITEM:
        for i in user.items_ids:
            find_item = mongo.db.equipments.find_one({"_id": ObjectId(i['_id'])})
            if find_item['type'] == "weapon":
                if find_item["attack"] < min["value"]:
                    min["_id"] = find_item["_id"]
                    min["value"] = find_item["attack"]
            else:
                if find_item["defense"] < min["value"]:
                    min["_id"] = find_item["_id"]
                    min["value"] = find_item["defense"]
        mongo.db.users.update_one({"username": session['username']}, {"$pull": {"items_ids": {'_id': str(min["_id"])}}})
        mongo.db.equipments.update_one({"_id": ObjectId(min["_id"])}, {"$set": {"owner_id": "0"}})
        return True
    else:
        return False
class User:
    id = ""
    username = ""
    password_hash = ""
    armor_ids = []
    weapon_id = ""
    items_ids = []
    gold = 0

    def __init__(self, id, username, password_hash, armor_ids, weapon_id, items_ids, gold):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.armor_ids = armor_ids
        self.weapon_id = weapon_id
        self.items_ids = items_ids
        self.gold = gold

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@app.route('/')
def index():
    if 'username' in session:
        users_dic[session['username']] = 0
        username = session['username']
        find_user = mongo.db.users.find_one({"username": username})
        user = User(id=find_user['_id'], username=find_user['username'],
                    password_hash=find_user["password_hash"], armor_ids=find_user["armor_ids"],
                    weapon_id=find_user["weapon_id"], items_ids=find_user['items_ids'], gold=find_user['gold'])
        attack = 0
        defense = 0
        if user.weapon_id == '0':
            weapon = "无"
            weapon_id = '0'
        else:
            find_weapon = mongo.db.equipments.find_one({"_id": ObjectId(user.weapon_id)})
            weapon = find_weapon['name']
            weapon_id = user.weapon_id
            attack = find_weapon['attack']
        armor = {}
        len = 0
        for i in user.armor_ids:
            find_armor = mongo.db.equipments.find_one({"_id": ObjectId(i['_id'])})
            armor[find_armor['name']] = i['_id']
            len = 1
            defense = defense + find_armor['defense']
        return render_template('index.html', username=user.username, weapon=weapon,
                               weapon_id=weapon_id, armor=armor, len=len, attack=attack,
                               defense=defense, gold=user.gold)
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    global users_dic
    if request.method == 'POST':
        find_user = mongo.db.users.find_one({"username": request.form['username']})
        if find_user is None:
            flash("用户不存在")
            return render_template("login.html")
        user = User(id=find_user['_id'], username=find_user['username'],
                    password_hash=find_user["password_hash"], armor_ids=find_user["armor_ids"],
                    weapon_id=find_user["weapon_id"], items_ids=find_user['items_ids'], gold=find_user['gold'])
        if not user.check_password(request.form['password']):
            flash("密码错误")
            return render_template("login.html")
        session["username"] = user.username
        users_dic[user.username] = 0
        return redirect(url_for('index'))
    return render_template("login.html", username=None)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        find_user = mongo.db.users.find_one({"username": request.form['username']})
        if find_user is not None:
            flash("用户已存在")
            return redirect(url_for('register'))
        user = User(id='0', username=request.form['username'], password_hash='0', armor_ids=[], weapon_id='0',
                    items_ids=[], gold=0)
        user.set_password(request.form['password'])
        insert_user = {
            'username': user.username,
            'password_hash': user.password_hash,
            'armor_ids': user.armor_ids,
            'weapon_id': user.weapon_id,
            'items_ids': user.items_ids,
            'gold': user.gold
        }
        mongo.db.users.insert_one(insert_user)
        find_user = mongo.db.users.find_one({'username': user.username})
        mongo.db.equipments.insert_many([
            {
                'name': career[request.form['career']]['weapon_name'],
                'type': 'weapon',
                'attack': career[request.form['career']]['weapon_attack'],
                'owner_id': str(find_user['_id']),
                'rare': 1
            },
            {
                'name': career[request.form['career']]['armors'][0]['armor_name'],
                'type': 'armor',
                'defense': career[request.form['career']]['armors'][0]['armor_defense'],
                'owner_id': str(find_user['_id']),
                'rare': 1
            },
            {
                'name': career[request.form['career']]['armors'][1]['armor_name'],
                'type': 'armor',
                'defense': career[request.form['career']]['armors'][1]['armor_defense'],
                'owner_id': str(find_user['_id']),
                'rare': 1
            }])
        find_items = mongo.db.equipments.find({'owner_id': str(find_user['_id'])})
        session["username"] = user.username
        for item in find_items:
            if item['type'] == 'weapon':
                equip_weapon(str(item['_id']))
            else:
                equip_armor(str(item['_id']))
        return redirect(url_for('index'))
    return render_template("register.html", username=None)


@app.route('/logout')
def logout():
    del users_dic[session['username']]
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/equipment/<oid>')
def equipment(oid):
    if 'username' in session:
        find_user = mongo.db.users.find_one({"username": session['username']})
        user = User(id=find_user['_id'], username=find_user['username'],
                    password_hash=find_user["password_hash"], armor_ids=find_user["armor_ids"],
                    weapon_id=find_user["weapon_id"], items_ids=find_user['items_ids'], gold=find_user['gold'])
        find_equipment = mongo.db.equipments.find_one(ObjectId(oid))
        name = find_equipment['name']
        type = find_equipment['type']
        rare = find_equipment['rare']
        equiped = 0
        if type == 'weapon':
            type = '武器'
            pattern = '攻击力'
            num = find_equipment['attack']
            if oid == user.weapon_id:
                equiped = 1
        else:
            type = '盔甲'
            pattern = '防御力'
            num = find_equipment['defense']
            if {"_id": oid} in user.armor_ids:
                equiped = 1
        return render_template('equipment.html', username=session['username'], name=name, type=type, pattern=pattern,
                               num=num, equiped=equiped, id=oid, rare=rare)
    else:
        return redirect(url_for('login'))


@app.route('/storage')
def storage():
    if 'username' in session:
        find_user = mongo.db.users.find_one({"username": session['username']})
        user = User(id=find_user['_id'], username=find_user['username'],
                    password_hash=find_user["password_hash"], armor_ids=find_user["armor_ids"],
                    weapon_id=find_user["weapon_id"], items_ids=find_user['items_ids'], gold=find_user['gold'])
        item = {}
        len = 0
        for i in user.items_ids:
            find_item = mongo.db.equipments.find_one({"_id": ObjectId(i['_id'])})
            item[find_item['name']] = i['_id']
            len = 1
        return render_template('storage.html', username=session['username'], item=item, len=len)
    else:
        return redirect(url_for('login'))


@app.route('/equip_weapon/<oid>')
def equip_weapon(oid):
    if 'username' in session:
        find_user = mongo.db.users.find_one({"username": session['username']})
        user = User(id=find_user['_id'], username=find_user['username'],
                    password_hash=find_user["password_hash"], armor_ids=find_user["armor_ids"],
                    weapon_id=find_user["weapon_id"], items_ids=find_user['items_ids'], gold=find_user['gold'])
        prev_weapon_id = user.weapon_id
        mongo.db.users.update_one({"username": session['username']}, {"$set": {"weapon_id": oid}})
        if prev_weapon_id != '0':
            is_full(user.username)
            mongo.db.users.update_one({"username": session['username']},
                                      {"$push": {"items_ids": {'_id': prev_weapon_id}}})
        mongo.db.users.update_one({"username": session['username']}, {"$pull": {"items_ids": {'_id': oid}}})
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route('/unequip_weapon')
def unequip_weapon():
    if 'username' in session:
        find_user = mongo.db.users.find_one({"username": session['username']})
        user = User(id=find_user['_id'], username=find_user['username'],
                    password_hash=find_user["password_hash"], armor_ids=find_user["armor_ids"],
                    weapon_id=find_user["weapon_id"], items_ids=find_user['items_ids'], gold=find_user['gold'])
        prev_weapon_id = user.weapon_id
        mongo.db.users.update_one({"username": session['username']}, {"$set": {"weapon_id": '0'}})
        is_full(user.username)
        mongo.db.users.update_one({"username": session['username']}, {"$push": {"items_ids": {'_id': prev_weapon_id}}})
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route('/equip_armor/<oid>')
def equip_armor(oid):
    if 'username' in session:
        find_user = mongo.db.users.find_one({"username": session['username']})
        user = User(id=find_user['_id'], username=find_user['username'],
                    password_hash=find_user["password_hash"], armor_ids=find_user["armor_ids"],
                    weapon_id=find_user["weapon_id"], items_ids=find_user['items_ids'], gold=find_user['gold'])
        if len(user.armor_ids) >= 2:
            flash("护甲已满，请卸下再装备")
        else:
            mongo.db.users.update_one({"username": session['username']}, {"$push": {"armor_ids": {'_id': oid}}})
            mongo.db.users.update_one({"username": session['username']}, {"$pull": {"items_ids": {'_id': oid}}})
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route('/unequip_armor/<oid>')
def unequip_armor(oid):
    if 'username' in session:
        find_user = mongo.db.users.find_one({"username": session['username']})
        user = User(id=find_user['_id'], username=find_user['username'],
                    password_hash=find_user["password_hash"], armor_ids=find_user["armor_ids"],
                    weapon_id=find_user["weapon_id"], items_ids=find_user['items_ids'], gold=find_user['gold'])
        mongo.db.users.update_one({"username": session['username']}, {"$pull": {"armor_ids": {'_id': oid}}})
        is_full(user.username)
        mongo.db.users.update_one({"username": session['username']}, {"$push": {"items_ids": {'_id': oid}}})
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route('/work')
def work():
    global users_dic
    if 'username' in session:
        find_user = mongo.db.users.find_one({"username": session['username']})
        user = User(id=find_user['_id'], username=find_user['username'],
                    password_hash=find_user["password_hash"], armor_ids=find_user["armor_ids"],
                    weapon_id=find_user["weapon_id"], items_ids=find_user['items_ids'], gold=find_user['gold'])
        if user.weapon_id == '0':
            flash("未装备武器！")
            return redirect(url_for('index'))
        else:
            if users_dic[user.username] == 1:
                find_weapon = mongo.db.equipments.find_one(ObjectId(user.weapon_id))
                attack = find_weapon['attack']
                attack = int(attack)
                mongo.db.users.update_one({'_id': user.id}, {"$inc": {"gold": attack}})
                flash("获得" + str(attack) + "金币！")
                users_dic[user.username] = 0
                return redirect(url_for('index'))
            else:
                flash("未到出击时间！")
                return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route('/explore')
def explore():
    global users_dic
    if 'username' in session:
        find_user = mongo.db.users.find_one({"username": session['username']})
        user = User(id=find_user['_id'], username=find_user['username'],
                    password_hash=find_user["password_hash"], armor_ids=find_user["armor_ids"],
                    weapon_id=find_user["weapon_id"], items_ids=find_user['items_ids'], gold=find_user['gold'])
        defense = 0
        if len(user.armor_ids) == 0:
            flash("未装备铠甲！")
            return redirect(url_for('index'))
        if users_dic[user.username] == 1:
            for i in user.armor_ids:
                find_armor = mongo.db.equipments.find_one({"_id": ObjectId(i['_id'])})
                defense = defense + find_armor['defense']
            defense = int(defense)
            rare = rare_list[weight_choice(weight_count(defense))]
            find_items = mongo.db.equipments.find({'rare': rare, 'owner_id': '0'})
            items = []
            for item in find_items:
                items.append(item)
            item = random.choice(items)
            is_full(user.username)
            mongo.db.users.update_one({"username": session['username']}, {'$push': {'items_ids': {'_id': str(item['_id'])}}})
            mongo.db.equipments.update_one({'_id': item['_id']}, {'$set': {'owner_id': str(user.id)}})
            flash("获得"+item['name']+"！")
            return redirect(url_for('index'))
        else:
            flash("未到探索时间！")
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route('/market')
def market():
    if 'username' in session:
        find_all = mongo.db.market.find()
        items = []
        for item in find_all:
            find_user = mongo.db.users.find_one({'_id': ObjectId(item['owner_id'])})
            item['owner_id'] = find_user['username']
            if item['type']=='weapon':
                item['type'] = '武器'
            else:
                item['type'] = '盔甲'
            items.append(item)
        return render_template('market.html', items=items, username=session['username'])
    else:
        return redirect(url_for('login'))


@app.route('/buy/<oid>')
def buy(oid):
    if 'username' in session:
        find_user = mongo.db.users.find_one({"username": session['username']})
        user = User(id=find_user['_id'], username=find_user['username'],
                    password_hash=find_user["password_hash"], armor_ids=find_user["armor_ids"],
                    weapon_id=find_user["weapon_id"], items_ids=find_user['items_ids'], gold=find_user['gold'])
        find_sell = mongo.db.market.find_one({"_id": ObjectId(oid)})
        if int(find_sell["prize"]) > user.gold:
            flash("金币不足")
            return redirect(url_for('market'))
        find_sell['owner_id'] = str(user.id)
        user.gold = user.gold - int(find_sell['prize'])
        del find_sell['prize']
        mongo.db.market.delete_one({"_id": ObjectId(oid)})
        mongo.db.equipments.insert_one(find_sell)
        is_full(user.username)
        mongo.db.users.update_one({"username": user.username}, {"$push": {"items_ids": {"_id": str(find_sell['_id'])}}})
        mongo.db.users.update_one({"username": user.username}, {"$set": {"gold": user.gold}})
        flash("成功购买"+find_sell['name']+"！")
        return redirect(url_for('market'))
    else:
        return redirect(url_for('login'))


@app.route("/off/<oid>")
def off(oid):
    if 'username' in session:
        find_user = mongo.db.users.find_one({"username": session['username']})
        user = User(id=find_user['_id'], username=find_user['username'],
                    password_hash=find_user["password_hash"], armor_ids=find_user["armor_ids"],
                    weapon_id=find_user["weapon_id"], items_ids=find_user['items_ids'], gold=find_user['gold'])
        find_sell = mongo.db.market.find_one({"_id": ObjectId(oid)})
        del find_sell['prize']
        mongo.db.market.delete_one({"_id": ObjectId(oid)})
        mongo.db.equipments.insert_one(find_sell)
        is_full(user.username)
        mongo.db.users.update_one({"username": user.username}, {"$push": {"items_ids": {"_id": str(find_sell['_id'])}}})
        return redirect(url_for('market'))
    else:
        return redirect(url_for('login'))


@app.route('/on/<oid>', methods=['GET', 'POST'])
def on(oid):
    if 'username' in session:
        if request.method == 'POST':
            find_user = mongo.db.users.find_one({"username": session['username']})
            user = User(id=find_user['_id'], username=find_user['username'],
                        password_hash=find_user["password_hash"], armor_ids=find_user["armor_ids"],
                        weapon_id=find_user["weapon_id"], items_ids=find_user['items_ids'], gold=find_user['gold'])
            find_item = mongo.db.equipments.find_one({"_id": ObjectId(oid)})
            find_item['prize'] = request.form['prize']
            mongo.db.market.insert_one(find_item)
            mongo.db.equipments.delete_one({"_id": ObjectId(oid)})
            mongo.db.users.update_one({"username": user.username}, {"$pull": {"items_ids": {"_id": oid}}})
            flash("出售成功")
            return redirect(url_for('index'))
        else:
            return render_template("on.html", username=session['username'])
    else:
        return redirect(url_for('login'))


app.run()
