import config
import bcrypt
from datetime import datetime
import time

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean

from sqlalchemy.orm import sessionmaker, scoped_session, relationship, backref

from flask.ext.login import UserMixin

# These are imported for uploading files
from flask import Flask, request, redirect, url_for
from werkzeug import secure_filename

engine = create_engine(config.DB_URI, echo=False)
session = scoped_session(sessionmaker(bind=engine,
                         autocommit = False,
                         autoflush = False))


Base = declarative_base()
Base.query = session.query_property()

# Validation lives here. The user table contains email and password info. User information about their campaign also lives here. 
class User(Base, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(64), nullable=False)
    password = Column(String(64), nullable=False)
    salt = Column(String(64), nullable=False)
    first_name = Column(String(16), nullable=False)
    last_name = Column(String(24), nullable=False)
    linkedin = Column(String(128), nullable=True)
    github = Column(String(128), nullable=True)
    twitter = Column(String(128), nullable=True)
    img = Column(String(128), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    approved = Column(Boolean, default=False)
    campaign = relationship("Campaign", uselist=False)
    kudoses = relationship("Kudoses", uselist=True)
  
    def set_password(self, password):
        self.salt = bcrypt.gensalt()
        password = password.encode("utf-8")
        self.password = bcrypt.hashpw(password, self.salt)

    def authenticate(self, password):
        password = password.encode("utf-8")
        return bcrypt.hashpw(password, self.salt.encode("utf-8")) == self.password


class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True)
    video = Column(String(128))
    deadline = Column(DateTime, nullable=False, default=datetime.now)
    #Float for money/bitcoin fractions?
    goal = Column(Integer, nullable=True)
    tagline = Column(String(128), nullable=True)
    description = Column(String(128), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    user_id = Column(Integer, ForeignKey("users.id"))
    approved = Column(Boolean, default=False)
    kudoses = relationship("Kudoses", uselist=True)
    user = relationship("User", backref="user")

    def time_remaining(self, currentDate):
        # remaining = self.deadline - currentDate
        remaining = self.deadline - datetime(2013, 12, 16)
        days = remaining.days
        if days <= 0:
            return "Completed"
        if days == 1:
            return remaining.seconds
        return days

    def numKudoses(self):
        return len(self.kudoses)

    def addKudos(self, user_id):
        if user_id == None:
            return False

        for kudos in self.kudoses:
            if kudos.user_id == user_id:
                return False

        newKudos = Kudoses(campaign_id=self.id, user_id=user_id)
        session.add(newKudos)
        session.commit()
        return True

    def hasKudosed(self, user_id):
        if user_id == None:
            return False
        for kudos in self.kudoses:
            if kudos.user_id == user_id:
                return True
        return False

    def removeKudos(self, user_id):
        delKudo = Kudoses.query.filter_by(user_id=user_id).one()
        session.delete(delKudo)
        session.commit()

class Kudoses(Base):
    __tablename__ = "kudoses"
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

class Supporters(Base):
    __tablename__ = "supporters"
    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", backref="supported")

    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    campaign = relationship("Campaign", backref=backref("supporters", uselist=True))

class Comments(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    comment = Column(String, nullable=True)
    kudos = Column(Boolean, default=False) 
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    posted_at = Column(DateTime, nullable=True, default=None)
    user = relationship("User", backref="comments")

    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    campaign = relationship("Campaign", backref=backref("comments", uselist=True))

# This creates the tables. drop_all is a hack to delete tables and recreate them. Needs a more permanent solution. 
def create_tables():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

def seed():
    user = User(email="dslevi12@gmail.com", first_name="Danielle", last_name="Levi", 
        linkedin="www.linkedin.com/in/dslevi/", github="https://github.com/dslevi", 
        twitter="https://twitter.com/DaniSLevi", img=None)
    user.set_password('python')
    session.add(user)

    camp = Campaign(video="http://www.youtube.com/watch?feature=player_detailpage&v=0byNU3RHhr8",
        goal=500, tagline="I want to learn how to program", description="I am a super cool programmer.",
        user_id=user.id)

    user.campaign = camp
    session.add(camp)
    session.add(user)

    session.commit()
 
if __name__ == "__main__":
    create_tables()
    seed()

