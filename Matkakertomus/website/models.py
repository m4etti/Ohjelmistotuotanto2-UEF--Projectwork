from sqlalchemy import ForeignKey, Integer
from . import db
from flask_login import UserMixin

class Matkaaja(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(45),unique=True)
    password = db.Column(db.String(45))
    etunimi = db.Column(db.String(45))
    sukunimi  = db.Column(db.String(45))
    nimimerkki = db.Column(db.String(45))
    paikkakunta = db.Column(db.String(45))
    esittely = db.Column(db.String(500))
    kuva = db.Column(db.String())
    matka = db.relationship('Matka', cascade="all, delete-orphan", backref='matkaaja', lazy='dynamic')

class Matkakohde (db.Model):
    idmatkakohde = db.Column(db.Integer, primary_key=True)
    kohdenimi = db.Column(db.String(45),unique=True)
    maa = db.Column(db.String(45))
    paikkakunta = db.Column(db.String(45))
    kuvateksti = db.Column(db.String(500))
    kuva = db.Column(db.String())
    tarina = db.relationship('Tarina', cascade="all, delete-orphan", backref='matkakohde', lazy='dynamic')
    
class Matka(db.Model):
    idmatka = db.Column(db.Integer, primary_key=True)
    idmatkaaja = db.Column(db.Integer, db.ForeignKey('matkaaja.id'))
    alkupvm = db.Column(db.String(45))
    loppupvm = db.Column(db.String(45))
    yksityinen = db.Column(db.Boolean)
    tarina = db.relationship('Tarina', cascade="all, delete-orphan", backref='matka', lazy='dynamic')
    
class Tarina(db.Model):
    idtarina = db.Column(db.Integer, primary_key=True)
    idmatka = db.Column(db.Integer, db.ForeignKey('matka.idmatka'))
    idmatkakohde = db.Column(db.Integer, db.ForeignKey('matkakohde.idmatkakohde'))
    pvm = db.Column(db.String(45))
    teksti = db.Column(db.String)
    kuva = db.relationship('Kuva', cascade="all, delete-orphan", backref='tarina', lazy='dynamic')
    
class Kuva(db.Model):
    idkuva = db.Column(db.Integer, primary_key=True)
    idtarina = db.Column(db.Integer, db.ForeignKey('tarina.idtarina'))
    kuva = db.Column(db.String())
        
        
    