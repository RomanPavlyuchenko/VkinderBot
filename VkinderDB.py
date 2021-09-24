import sqlalchemy as sq
from sqlalchemy.orm import Session

from database_model import User, ViewedUser, SearchedUser, SearchParams, Base


class VkinderDB:
    session = None
    engine = None
    Base = Base

    def __init__(self, connect):
        self.engine = sq.create_engine(connect)
        self.session = Session(bind=self.engine)

    def init_db(self):
        self.Base.metadata.create_all(self.engine)
        print('db_created')

    def drop_all(self):
        self.Base.metadata.drop_all(self.engine)
        print('bd was drop')

    def get_user(self, user_id) -> User:
        user = self.session.get(User, user_id)
        return user

    def add_user(self, user_data):
        new_user = User(
            id=user_data['id'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            gender=user_data['gender']
        )
        self.session.add(new_user)
        self.session.commit()

    def set_search_params(self, user_id, search_params):
        user = self.get_user(user_id)
        if user.params:
            user.params.b_year = search_params['b_year']
            user.params.city = search_params['city']
            user.params.status = search_params['status']
        else:
            new_params = SearchParams(
                user_id=user.id,
                b_year=search_params['b_year'],
                city=search_params['city'],
                status=search_params['status']
            )
            self.session.add(new_params)
        self.session.commit()

    def get_search_params(self, user_id):
        user = self.session.get(User, user_id)
        bd_params = user.params
        if bd_params:
            params = {
                'city': bd_params.city,
                'status': bd_params.status,
                'gender': user.gender,
                'b_year': bd_params.b_year
            }
            return params
        else:
            return None

    def add_viewed(self, user_id, viewed_id):
        viewed = self.session.get(ViewedUser, viewed_id)
        if viewed:
            viewed.users.append(self.get_user(user_id))
        else:
            viewed = ViewedUser(id=viewed_id)
            user = self.get_user(user_id)
            viewed.users.append(user)
        self.session.commit()

    def get_searched_id(self, user_id):
        """
        Возвращает id страницы найденной для пользователя, если найденных нет, то возвращает None
        """
        user = self.get_user(user_id)
        if user.searched:
            searched = user.searched.pop()
            self.add_viewed(user_id, searched.id)
            return searched.id
        else:
            return None

    def add_searched_users(self, user_id, searched_list_id):
        """
        Сохраняет найденные варианты для пользователя в базу
        """
        user = self.get_user(user_id)
        exist_searched_list = [i.id for i in self.session.query(User).join(SearchedUser, User.searched).filter(
            User.id == user.id).all()]
        exist_viewed_list = [i.id for i in
                             self.session.query(User).join(ViewedUser, User.viewed).filter(User.id == user.id).all()]
        temp_list = []

        for search_id in searched_list_id:
            if search_id in exist_searched_list or search_id in exist_viewed_list:
                continue
            else:
                searched = self.session.get(SearchedUser, search_id)
                if searched:
                    searched.users.append(search_id)
                else:
                    searched = SearchedUser(id=search_id)
                    searched.users.append(user)
                temp_list.append(searched)

        self.session.add_all(temp_list)
        self.session.commit()