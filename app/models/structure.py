from app import db
from datetime import datetime
import uuid

# Association tables for Many-to-Many relationships if needed, 
# but User.py defines association tables for User-Org and User-Role.
# Here we probably need Resource-Org and Resource-Role?
# user.py: resources += [res for org in current_user.organizations for res in org.resources if org.resources]
# So Organization has 'resources'.

role_resource_table = db.Table('SYROLE_SYRESOURCE', db.Model.metadata
    , db.Column('SYROLE_ID', db.String, db.ForeignKey('SYROLE.ID'))
    , db.Column('SYRESOURCE_ID', db.String, db.ForeignKey('SYRESOURCE.ID'))
)

organization_resource_table = db.Table('SYORGANIZATION_SYRESOURCE', db.Model.metadata
    , db.Column('SYORGANIZATION_ID', db.String, db.ForeignKey('SYORGANIZATION.ID'))
    , db.Column('SYRESOURCE_ID', db.String, db.ForeignKey('SYRESOURCE.ID'))
)

class Resource(db.Model):
    __tablename__ = 'SYRESOURCE'
    ID = db.Column(db.String(36), primary_key=True)
    NAME = db.Column(db.String(100))
    URL = db.Column(db.String(200))
    PERMS = db.Column(db.String(100))
    
    def to_json(self):
        return {
            'id': self.ID,
            'name': self.NAME,
            'url': self.URL,
            'perms': self.PERMS
        }

class Role(db.Model):
    __tablename__ = 'SYROLE'
    ID = db.Column(db.String(36), primary_key=True)
    NAME = db.Column(db.String(100))
    
    resources = db.relationship('Resource',
                                secondary=role_resource_table,
                                backref=db.backref('roles', lazy='dynamic'))

    def to_json(self):
        return {
            'id': self.ID,
            'name': self.NAME
        }

class Organization(db.Model):
    __tablename__ = 'SYORGANIZATION'
    ID = db.Column(db.String(36), primary_key=True)
    NAME = db.Column(db.String(100))
    
    resources = db.relationship('Resource',
                                secondary=organization_resource_table,
                                backref=db.backref('organizations', lazy='dynamic'))

    def to_json(self):
        return {
            'id': self.ID,
            'name': self.NAME
        }
