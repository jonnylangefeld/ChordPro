
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tabledef import *
from passlib.hash import sha256_crypt

engine = create_engine('sqlite:///users.db', echo=True)

# create a Session
Session = sessionmaker(bind=engine)
session = Session()

user = User("sven",sha256_crypt.encrypt('Ch0rdPr0'))
session.add(user)

# commit the record the database
session.commit()
