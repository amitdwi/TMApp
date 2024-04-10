from .mongo import db

def fetch_jwt_token(context):
    tokens = db['token']
    tokens.find_one({'user': context["user_id"]})
    print(result)
    if result :
        return result["jwt"]
    return False

def user_auth_check(workspace, user):
    if fetch_jwt_token(workspace, user):
        return True
    return False