from flask_restful import Resource
from flask import request

from email_validator import validate_email, EmailNotValidError
from utils import create_hash_passwrod, compare_hash_password
from mysql.connector import Error
from mysql_connection import get_connection

from flask_jwt_extended import create_access_token, get_jwt, jwt_required


# 유저 회원가입
class UserRegisterResource(Resource):
    def post(self):
        
        # body - {
        #     email : "222@naver.com",
        #     nickname : "닉네임",
        #     name : "이름임",
        #     password : "1234"
        # }
        
        data = request.get_json()
        check_list = ['email', 'password', 'name', 'nickname']
        for check in check_list:
            if check not in data:
                return {
                    'result' : 'fail',
                    'error' : '필수 항목을 확인하세요.'
                }, 400

        try:
            validate_email(data['email'])
        except EmailNotValidError as e:
            return {
                'result' : 'fail',
                'error' : str(e)
            }, 401
            
        if len(data['password']) < 6:
            return {
                'result' : 'fail',
                'error' : '비밀번호는 최소 6자리 이상입니다.'
            }, 402
        
        # 비밀번호 암호화
        hash_password = create_hash_passwrod(data['password'])

        try:
            connection = get_connection()

            query = """
                select *
                from user
                where email = %s;
            """
            record = (data['email'], )
            cursor = connection.cursor()
            cursor.execute(query, record)
            result_list = cursor.fetchall()
            if len(result_list) > 0:
                return {
                    'result' : 'fail',
                    'error' : '이미 있는 회원입니다.'
                }, 403
            
            query = '''
                insert into user
                (email, nickname, name, password)
                values
                (%s, %s, %s, %s);
            '''
            record = (data['email'], data['nickname'], data['name'], hash_password)

            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()

            cursor.close()
            connection.close()
            
        except Error as e:
            return {
                'result' : 'fail',
                'error' : str(e)
            }, 500

        return {
            'result' : 'success'
        }
        

# 유저 로그인
class UserLoginResource(Resource):
    def post(self):

        # body - {
        #         "email" : "222@naver.com",
        #         "password" : "1234"
        #     }
        data = request.get_json()

        try :
            connection = get_connection()
            
            query = '''
                select * 
                from user
                where email = %s;
            '''
            record = (data['email'], )
            
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()

            if len(result_list) == 0:
                return {
                    'result' : 'fail',
                    'error' : '회원이 없습니다.'
                },  400

            if not compare_hash_password(data['password'], result_list[0]['password']):
                return {
                    'result' : 'fail',
                    'error' : '비밀번호가 다릅니다.'
                },  401
            
            cursor.close()
            connection.close()

        except Error as e:
            return {
                'result' : 'fail',
                'error' : str(e)
            }, 500

        accessToken = create_access_token(result_list[0]['id'])

        return {
            'result' : 'success',
            'accessToken' : accessToken
        }
    

# 유저 로그아웃
jwt_blocklist = set()
class UserLogoutResource(Resource):
    @jwt_required()
    def delete(self):
        jti = get_jwt()['jti']
        jwt_blocklist.add(jti)

        return {
            'result' : 'success'
        }
    
class UserEmailFindResource(Resource):
    def post(self):

        data = request.get_json()

        try:
            connection = get_connection()

            query = '''
                select email
                from user
                where name = %s and nickname = %s;
            '''
            record = (data['name'], data['nickname'])
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result = cursor.fetchall()

            if len(result) == 0:
                return {
                    'result' : 'fail',
                    'error' : '찾는 이메일이 없습니다.'
                }, 400

            cursor.close()
            connection.close()

        except Error as e:
            return {
                'result' : 'fail',
                'error' : str(e)
            }, 500


        
        return {
            'result' : 'success',
            'email' : result[0]['email']
        }
    
