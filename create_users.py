
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tabledef import *
from passlib.hash import sha256_crypt

engine = create_engine('sqlite:///users.db', echo=True)

# create a Session
Session = sessionmaker(bind=engine)
session = Session()

user = User("admin",sha256_crypt.encrypt('admin'))
session.add(user)

# commit the record the database
session.commit()
