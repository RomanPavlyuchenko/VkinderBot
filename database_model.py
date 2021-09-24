import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = sq.Column(sq.Integer, primary_key=True)
    first_name = sq.Column(sq.String)
    last_name = sq.Column(sq.String)
    gender = sq.Column(sq.Integer)
    # b_year = sq.Column(sq.Integer)
    # searched_users = relationship('SearchedUser', secondary='user_to_searched_user')
    params = relationship('SearchParams', uselist=False, backref='user')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class SearchParams(Base):
    __tablename__ = 'search_params'
    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('user.id'))
    b_year = sq.Column(sq.Integer)
    city = sq.Column(sq.String)
    status = sq.Column(sq.Integer)
    gender = sq.Column(sq.String)


user_to_searched_user = sq.Table(
    'user_to_searched_user', Base.metadata,
    sq.Column('user_id', sq.Integer, sq.ForeignKey('user.id')),
    sq.Column('searched_user_id', sq.Integer, sq.ForeignKey('searched_user.id')),
)


class SearchedUser(Base):
    __tablename__ = 'searched_user'
    id = sq.Column(sq.Integer, primary_key=True)
    # first_name = sq.Column(sq.String)
    # last_name = sq.Column(sq.String)
    # b_date = sq.Column(sq.Date)
    users = relationship(User, secondary=user_to_searched_user, backref='searched')

    def __str__(self):
        return str(self.id)


user_to_viewed_user = sq.Table(
    'user_to_viewed_user', Base.metadata,
    sq.Column('user_id', sq.Integer, sq.ForeignKey('user.id')),
    sq.Column('viewed_user_id', sq.Integer, sq.ForeignKey('viewed_user.id'))
)


class ViewedUser(Base):
    __tablename__ = 'viewed_user'
    id = sq.Column(sq.Integer, primary_key=True)
    users = relationship(User, secondary=user_to_viewed_user, backref='viewed')

    def __str__(self):
        return str(self.id)