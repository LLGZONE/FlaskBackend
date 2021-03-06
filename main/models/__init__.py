from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

from main.models import case
from main.models import location
from main.models import user
from main.models import TokenBlacklist
from flask_jwt_extended import decode_token
from main.models.TokenBlacklist import TokenBlacklist

def _timestamp_to_datetime(timestamp):
    return datetime.fromtimestamp(timestamp)

def add_token_to_database(encoded_token, identity_claim):
    decoded_token = decode_token(encoded_token)
    db_token = TokenBlacklist(
        jti=decoded_token['jti'],
        token_type=decoded_token['type'],
        user_identity=decoded_token[identity_claim],
        expires=_timestamp_to_datetime(decoded_token['exp']),
        revoked=False
    )
    db_token.save()

def is_token_revoked(decoded_token):
    jti = decoded_token['jti']
    try:
        token = TokenBlacklist.query.filter_by(jti=jti).one()
        return token.revoked
    except NoResultFound:
        return True

def get_user_tokens(user_identity):
    return TokenBlacklist.query.filter_by(user_identity=user_identity).all()


def revoke_token(jti, user):
    try:
        token = TokenBlacklist.query.filter_by(jti=jti, user_identity=user).one()
        token.revoked = True
        db.session.commit()
    except NoResultFound:
        raise TokenNotFound("Could not find the token {}".format(token_id))


def unrevoke_token(token_id, user):
    try:
        token = TokenBlacklist.query.filter_by(id=token_id, user_identity=user).one()
        token.revoked = False
        db.session.commit()
    except NoResultFound:
        raise TokenNotFound("Could not find the token {}".format(token_id))


def prune_database():
    now = datetime.now()
    expired = TokenBlacklist.query.filter(TokenBlacklist.expires < now).all()
    for token in expired:
        db.session.delete(token)
    db.session.commit()
