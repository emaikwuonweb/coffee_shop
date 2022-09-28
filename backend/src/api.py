from dataclasses import replace
import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from jose import jwt

from .database.models import db_drop_and_create_all, setup_db, Drink, db
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


db_drop_and_create_all()

# ROUTES

@app.route('/drinks')
def list_drinks():
    query = Drink.query.all()
    drinks = [drink.short() for drink in query]
    return jsonify({
        "success": True,
        "drinks": drinks
    })


@app.route('/drinks-detail')
@requires_auth(permission='get:drinks-detail')
def drink_detail(jwt):
    query = Drink.query.all()
    drinks = [drink.long() for drink in query]
    return jsonify({
        "success": True,
        "drinks": drinks
    })


@app.route('/drinks', methods=['POST'])
@requires_auth(permission='post:drinks')
def add_drink(jwt):
    req_title = request.get_json()['title']
    req_recipe= json.dumps(request.get_json()['recipe'])
    drink_exists = Drink.query.filter(Drink.title==req_title).one_or_none()
    if drink_exists is None:
        drink = Drink(
            title=req_title,
            recipe=req_recipe
        )
        drink.insert()
        if drink:
            return jsonify({
                'success': True,
                'drinks': drink.long()
            }), 201
        abort(500)
    abort(409)
       

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth(permission='patch:drinks')
def update_drink(jwt, id=id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    if drink is not None:
        drink.title = request.get_json()['title']
        drink.recipe = json.dumps(request.get_json()['recipe'])
        drink.update()
        return jsonify({
            'success': True,
            'drinks': drink.long()
        })
    abort(404)


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth(permission='delete:drinks')
def delete_drink(jwt, id=id):
    drink = Drink.query.filter(Drink.id==id).one_or_none()
    if drink is None:
        abort(404)
    drink.delete()
    return jsonify({
        "success": True,
        "delete": id
    })

# Error Handling
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Unauthorized"
    }), 401


@app.errorhandler(409)
def request_conflict(error):
    return jsonify({
        "success": False,
        "error": 409,
        "message": "Request conflict"
    }), 409


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "Internal server error"
    }), 500


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "Bad request"
    }), 400


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        'success': False,
        'error': error.status_code,
        'message': error.error
    }), error.status_code