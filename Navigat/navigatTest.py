from flask import Flask
from flask import  render_template
from flask_sqlalchemy import SQLAlchemy
from flask import request,jsonify
import pymysql
import datetime
import json
from werkzeug.exceptions import HTTPException
from flask_cors import *

pymysql.install_as_MySQLdb()


app = Flask(__name__)
# CORS(app, supports_credentials=True)
# r'/*' 是通配符，让本服务器所有的URL 都允许跨域请求
CORS(app, resources=r'/*')

# 载入配置文件
#app.config.from_pyfile('config.ini')
#指定数据库连接还有库名
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:sangfordb@200.200.169.189:3305/Navigat?charset=utf8'
# 指定配置，用来省略提交操作
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
#
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 建立数据库对象
db = SQLAlchemy(app)


class ApiException(HTTPException):
    code = 500
    errmsg = 'sorry ,we make a mistake'
    def __init__(self,code=None,errmsg=None,id=None,header=None):
        if code:
            self.code = code
        if errmsg:
            self.errmsg = errmsg
        super(ApiException,self).__init__(errmsg,None)

    def get_body(self, environ=None):
        body=dict(
            errmsg=self.errmsg
        )
        text = json.dumps(body)
        return text
    def get_headers(self, environ=None) :
        return [('Content-Type','application/json')]
    @staticmethod
    def get_url_no_param():
        full_url = str(request.full_path)
        main_path = full_url.split('?')
        return  main_path[0]

class ClientTypeError(ApiException):
    code = 400
    errmsg = 'client is invalid'

class ParameterException(ApiException):
    code = 400
    errmsg = 'invalid parameter'

@app.errorhandler(Exception)
def framework_error(e):
    if isinstance(e, ApiException):
        return e
    if isinstance(e,HTTPException):
        code=e.code
        errmsg=e.description
        return ApiException(code,errmsg)
    else:
        return e



# 建立数据库类，用来映射数据库表,将数据库的模型作为参数传入
class Navigat(db.Model):
    # 定义表名
    __tablename__ = 'navigat'
    # 定义字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64))
    sort = db.Column(db.Integer)
    content = db.Column(db.String(1000))
    parentid = db.Column(db.Integer)
    update_date = db.Column(db.DATE)

def get_info_byID(id):
    navigat_list = []
    sql = 'select * from navigat where id = %d order by sort' % id
    items = db.session.execute(sql)
    for item in items:
        navigat_list.append({
            "id": item.id,
            "name": item.name,
            "sort": item.sort,
            "content": item.content,
            "parentid": item.parentid
        })

    return navigat_list

#新建
def index(name=None,sort=None,content=None,parentid=None):

    now = datetime.datetime.now()
    # 声明对象
    navigat = Navigat(name=name,sort=sort,content=content,parentid=parentid,update_date=now)
    # 调用添加方法
    db.session.add(navigat)
    db.session.flush()
    id = navigat.id
    # 提交入库
    db.session.commit()

    result = {"id": id, "errmsg": None}
    return result

#更改
def edit_navigat(id,newdata):
    # 根据某个字段做修改操作
    # 翻译为 update user set name = '张三' where id = 2

    if get_info_byID(id):
        Navigat.query.filter_by(id=id).update(newdata)
    else:
        raise ApiException(errmsg="id不存在")
    # 提交入库
    db.session.commit()
    result={"errmsg": None}
    return result

#删除
def del_navigat(id):
    # 根据某个字段做删除,filter_by可以理解为where条件限定
    # 翻译为 delete from user where id = 1

    if get_info_byID(id):
         Navigat.query.filter_by(id=id).delete()
        # 提交入库
         db.session.commit()
    else:
        raise ApiException(errmsg="id不存在")
    errmsg = None
    result = {"errmsg": errmsg}
    return result

# 数据库的查询操作（查）
def select_navigat(id=None,name=None):

    navigat_list = []
    if id==None and name==None:
        #全量获取数据
        try:
            nlist = Navigat.query.all()
        except Exception as e:
            db.session.rollback()
            result = {
                "list": "",
                "errmsg": "获取数据失败"
            }
            return result
        for item in nlist:
            navigat_list.append({
            "id": item.id,
            "name": item.name,
            "sort": item.sort,
            "content": item.content,
            "parentid": item.parentid
        })
        result = {
            "list": navigat_list,
             "errmsg": None
            }
        return result

    if id!=None and name==None:
        #根据id查询所有的子项
        try:
            sql='select * from navigat where parentid = %d order by sort' % id
            items = db.session.execute(sql)
        except TypeError as e:
            print(e)
            db.session.rollback()
            result = {
                "list": "",
                "errmsg": "数据类型错误，%s" % (e)
            }
            return result
        except Exception as e:
            db.session.rollback()
            result = {
                "list": "",
                "errmsg": "获取数据失败，%s"%(e)
            }
            return result
        for item in items:
            navigat_list.append({
                "id": item.id,
                "name": item.name,
                "sort": item.sort,
                "content": item.content,
                "parentid": item.parentid
            })

        result = {
                "list": navigat_list,
                "errmsg": None
        }

        return result

    if id==None and name!=None:
        #根据姓名模糊查询
        name="%"+name+"%"
        try:
            nlist = Navigat.query.filter(Navigat.name.ilike(name))
        except Exception as e:
            db.session.rollback()
            result = {
                "list": "",
                "errmsg": "获取数据失败，%s"%(e)
            }
            return  result

        for item in nlist:
            navigat_list.append({
            "id": item.id,
            "name": item.name,
            "sort": item.sort,
            "content": item.content,
            "parentid": item.parentid
        })
        result = {
            "list": navigat_list,
            "errmsg": None
        }
        return result






@app.route('/hello/')
def hello_world():
    return 'Hello World!'

#新建
@app.route('/setNavigat',methods=['POST'])
def setNavigat():
    #请求的数据格式 ： {"name":"客户","sort":10,"content":"www.bai","parentid":1}
    #curl -H "Content-Type: application/json" -X POST -d '{"name":"hello,it is me","sort":10,"content":"www.bai","parentid":1}' http://200.200.168.48:2333/setNavigat

    data = request.get_json()
    if 'name' in data and 'sort' in data and 'content' in data and 'parentid' in data :
        name = data['name']
        sort = data['sort']
        content = data['content']
        parentid = data['parentid']
    else:
        raise ParameterException()

    # if name==None or sort==None :
    #     return
    result = index(name,sort,content,parentid)
    result = json.dumps(result)
    return result

#编辑
@app.route('/updateNavigat',methods=['POST'])
def updateNavigat():
    # 请求的数据格式 ： {"id":5,"name":"客户","sort":10,"content":"www.bai",parentid:1}
    #curl -H "Content-Type: application/json" -X POST -d '{"id":5,"name":"客户","sort":10,"content":"www.bai"}' http://200.200.168.48:2333/updateNavigat

    newdata = request.get_json()
    if 'id' in newdata :
        id = newdata["id"]
    else:
        raise ParameterException()

    del newdata['id']
    result = edit_navigat(id,newdata)
    result = json.dumps(result)
    return result

#删除
'''
删除逻辑：先判断是否有子节点，如果没有子节点，直接删除
if 有子节点 & 有父节点 将子节点的parentid修改为父节点
if 有子节点 & 无父节点  不允许删除
'''
@app.route('/delNavigat',methods=['POST'])
def delNavigat():
    #curl -H "Content-Type: application/json" -X POST -d '{"id":9}' http://200.200.168.48:2333/delNavigat
    newdata = request.get_json()
    id = newdata["id"]
    navigatlist = select_navigat(id)
    lists = navigatlist['list']
    if lists:
        parentid = get_info_byID(id)[0]['parentid']
        if parentid:
            #双有
            for list  in lists:
                # {"id":33,"parentid":31}
                edit_navigat(id=list['id'],newdata={"parentid":parentid})
            navigatlist=select_navigat(id)
            if navigatlist['list']:
                raise ApiException(errmsg="处理失败，请稍后再试")
            else:
                result = del_navigat(id)
        else:
            raise ApiException(errmsg="根目录不允许删除")
    else:
        result = del_navigat(id)

    result = json.dumps(result)
    return result
#全量获取数据
@app.route('/getAllNavigat',methods=['GET'])
def getAllNavigat():
    # return render_template('Navigat.json')  #返回模板数据
    #curl -H "Content-Type: application/json" -X GET -d '{}' http://200.200.168.48:2333/getAllNavigat
    result = select_navigat()
    result = json.dumps(result)
    return result

#获取所有项
@app.route('/getNavigatbyId',methods=['POST'])
def getNavigatbyId():
    #curl -H "Content-Type: application/json" -X POST -d '{"id":"客户"}' http://200.200.168.48:2333/getNavigatbyId
    data = request.get_json()
    id = data["id"]
    result = select_navigat(id=id)
    result = json.dumps(result)
    return result

#搜索
@app.route('/searchNavigatbyName',methods=['POST'])
def searchNavigatbyName():
    #curl -H "Content-Type: application/json" -X POST -d '{"key":"客户"}' http://200.200.168.48:2333/searchNavigatbyName
    data = request.get_json()
    name = data["key"]
    result = select_navigat(name=name)
    result = json.dumps(result)
    return result

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=2333,debug=True)


