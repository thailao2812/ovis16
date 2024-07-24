# -*- coding: utf-8 -*-
import jwt
from datetime import datetime, timedelta
import os

class JWTAuth:
  def generate_token(self, user_id):
    try:
      payload = {
        'sub': user_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=60)
      }

      jwt_string = jwt.encode(payload, 
        '@pi_nedcoffee_mobi_@pp#', 
        algorithm='HS256')
      return jwt_string
    except Exception as e:
      return str(e)

  @staticmethod
  def decode_token(token):
    try:
      payload = jwt.decode(token, '@pi_nedcoffee_mobi_@pp#', algorithms='HS256')
      return payload
    except jwt.ExpiredSignatureError:
      return "Expired token. Please login to get a new token"
    except jwt.InvalidTokenError:
      return "Invalid token. Please register or login"
# os.getenv('SECRET')