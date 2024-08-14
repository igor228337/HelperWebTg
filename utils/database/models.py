import json
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Float, Text, and_, case, inspect, select, Boolean, update, event, BIGINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import validates, selectinload, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from config import PG_LINK, logger


engine = create_async_engine(PG_LINK, echo=True)
Base = declarative_base()

def id_column_type():
    """
    Определяет тип столбца id в зависимости от используемого диалекта базы данных.
    
    Returns:
        sqlalchemy.types.TypeEngine: Тип столбца id.
    """
    return Integer() if engine.dialect.name == 'sqlite' else BIGINT

class User(Base):
    """
    Модель пользователя.

    Attributes:
        id (int): Уникальный идентификатор пользователя.
        telegram_id (int): Идентификатор пользователя в Telegram.
        username (str): Имя пользователя в Telegram.
        is_admin (bool): Флаг, указывающий, является ли пользователь администратором.
        is_ban (bool): Флаг, указывающий, забанен ли пользователь.
    """
    __tablename__ = 'users'
    id = Column(id_column_type(), primary_key=True, autoincrement=True, index=True)
    telegram_id = Column(id_column_type(), unique=True, nullable=False, index=True)
    username = Column(String, nullable=True, index=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    is_ban = Column(Boolean, nullable=False, default=False)

    @staticmethod
    async def has_completed_or_canceled_orders(session, user_id: int) -> bool:
        """
        Проверяет, есть ли у пользователя хотя бы один заказ со статусом "Выполнен" или "Расторгнут".

        Args:
            session (AsyncSession): Сессия базы данных.
            user_id (int): Идентификатор пользователя.

        Returns:
            bool: True, если у пользователя есть хотя бы один заказ со статусом "Выполнен" или "Расторгнут", иначе False.
        """
        user: User = await User.find_user_by_telegram_id(session, user_id)
        check_existing_query = select(Review).where(Review.user_id == user.id)
        existing_result = await session.execute(check_existing_query)
        if existing_result.scalars().first() is not None:
            return False

        query = select(UserRequest).where(
            and_(
                UserRequest.user_id == user.id,
                UserRequest.status.in_(['Выполнен', 'Расторгнут'])
            )
        )
        result = await session.execute(query)
        return result.scalars().first() is not None

    @staticmethod
    async def is_user_banned(session: AsyncSession, telegram_id: int) -> bool:
        user: User = await User.find_user_by_telegram_id(session, telegram_id)
        if not user:
            return False
        return user.is_ban

    @staticmethod
    async def make_admin_by_username(session, username):
        """
        Назначает пользователя администратором по его имени пользователя.

        Args:
            session (AsyncSession): Сессия базы данных.
            username (str): Имя пользователя.

        Returns:
            bool: True, если пользователь был успешно назначен администратором, иначе False.
        """
        query = update(User).where(User.username == username).values(is_admin=True).returning(User.id)
        result = await session.execute(query)
        updated_user_id = result.scalars().first()
        return updated_user_id is not None
    
    @staticmethod
    async def get_admin_telegram_ids(session):
        """
        Получает идентификаторы Telegram всех администраторов.

        Args:
            session (AsyncSession): Сессия базы данных.

        Returns:
            list: Список идентификаторов Telegram администраторов.
        """
        query = select(User.telegram_id).where(User.is_admin == True)
        result = await session.execute(query)
        admin_telegram_ids = result.scalars().all()
        return admin_telegram_ids
    
    @staticmethod
    async def is_user_registered(session, telegram_id: int) -> bool:
        """
        Проверяет, зарегистрирован ли пользователь по его идентификатору Telegram.

        Args:
            session (AsyncSession): Сессия базы данных.
            telegram_id (int): Идентификатор Telegram пользователя.

        Returns:
            bool: True, если пользователь зарегистрирован, иначе False.
        """
        query = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        return user is not None
    
    @staticmethod
    async def find_user_by_telegram_id(session, telegram_id: int):
        """
        Находит пользователя по его идентификатору Telegram.

        Args:
            session (AsyncSession): Сессия базы данных.
            telegram_id (str): Идентификатор Telegram пользователя.

        Returns:
            User: Объект пользователя или None, если пользователь не найден.
        """
        query = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        user = result.scalars().first()
        return user
    
    @staticmethod
    async def find_user_by_telegram_username(session, username: str):
        """
        Находит пользователя по его имени пользователя в Telegram.

        Args:
            session (AsyncSession): Сессия базы данных.
            username (str): Имя пользователя в Telegram.

        Returns:
            User: Объект пользователя или None, если пользователь не найден.
        """
        query = select(User).where(User.username == username)
        result = await session.execute(query)
        user = result.scalars().first()
        return user

class Distributor(Base):
    """
    Модель распространителя.

    Attributes:
        id (int): Уникальный идентификатор распространителя.
        user_id (int): Идентификатор пользователя, связанного с распространителем.
        balance (float): Баланс распространителя.
        promo_codes (relationship): Связь с промокодами, принадлежащими распространителю.
    """
    __tablename__ = 'distributors'
    id = Column(id_column_type(), primary_key=True, autoincrement=True)
    user_id = Column(id_column_type(), ForeignKey('users.id'), unique=True, nullable=False)
    balance = Column(Float, default=0.0)
    promo_codes = relationship('PromoCode', back_populates='distributor')

    @staticmethod
    async def add_minus_money_dist(session, telegram_id: int, money: float):
        """
        Добавляет или снимает деньги с баланса распространителя.

        Args:
            session (AsyncSession): Сессия базы данных.
            telegram_id (str): ID пользователя в Telegram.
            money (float): Сумма денег для добавления или снятия.

        Returns:
            bool: True, если операция прошла успешно, иначе False.
        """
        async with session.begin():
            distrib = await Distributor.find_distributor_by_telegram_id(session, telegram_id=telegram_id)
            if money > 0:
                distrib.balance += money
            elif money < 0:
                if distrib.balance < -money:
                    return False
                distrib.balance -= -money
            
            await Transaction.record_transaction(session, distributor_id=distrib.id, amount=money, comment="Пополнение" if money > 0 else "Снятие средств")
        return True
    
    @staticmethod
    async def update_by_id(session, dist_id: int, **kwargs):
        """
        Обновляет информацию о распространителе по его идентификатору.

        Args:
            session (AsyncSession): Сессия базы данных.
            dist_id (int): Идентификатор распространителя.
            **kwargs: Аргументы для обновления.
        """
        query = update(Distributor).where(Distributor.id == dist_id).values(**kwargs)
        await session.execute(query)

    @staticmethod
    async def find_distributor_by_telegram_id(session, telegram_id: int):
        """
        Находит распространителя по идентификатору Telegram пользователя.

        Args:
            session (AsyncSession): Сессия базы данных.
            telegram_id (str): Идентификатор Telegram пользователя.

        Returns:
            Distributor: Объект распространителя или None, если распространитель не найден.
        """
        query = (
            select(Distributor)
            .join(User, Distributor.user_id == User.id)
            .where(User.telegram_id == telegram_id)
        )
        result = await session.execute(query)
        distributor = result.scalars().first()
        return distributor
    
    @staticmethod
    async def find_promo_codes_by_distributor_id(session, distributor_id: int):
        """
        Находит все промокоды, принадлежащие распространителю по его идентификатору.

        Args:
            session (AsyncSession): Сессия базы данных.
            distributor_id (int): Идентификатор распространителя.

        Returns:
            list: Список промокодов или пустой список, если промокоды не найдены.
        """
        query = (
            select(Distributor)
            .options(selectinload(Distributor.promo_codes))
            .where(Distributor.id == distributor_id)
        )
        result = await session.execute(query)
        distributor = result.scalars().first()
        return distributor.promo_codes if distributor else []

    @staticmethod
    async def get_order_statistics(session, distributor_id: int) -> dict:
        """
        Получает статистику заказов распространителя по его идентификатору.

        Args:
            session (AsyncSession): Сессия базы данных.
            distributor_id (int): Идентификатор распространителя.

        Returns:
            dict: Статистика заказов в формате {статус: количество}.
        """
        query = (
            select(UserRequest.status, func.count(UserRequest.id))
            .join(PromoCode, UserRequest.user_id == PromoCode.distributor_id)
            .where(PromoCode.distributor_id == distributor_id)
            .group_by(UserRequest.status)
        )
        result = await session.execute(query)
        statistics = {row[0]: row[1] for row in result.all()}
        return statistics
    
    @staticmethod
    async def get_user_for_distributor(session, distributor_id):
        distributor = await session.execute(select(Distributor).where(Distributor.id == distributor_id))
        distributor = distributor.scalars().first()
        if not distributor:
            return None
        user = await session.execute(select(User).where(User.id == distributor.user_id))
        user = user.scalars().first()
        return user

class PromoCode(Base):
    """
    Модель промокода.

    Attributes:
        id (int): Уникальный идентификатор промокода.
        code (str): Код промокода.
        distributor_id (int): Идентификатор распространителя, к которому принадлежит промокод.
        distributor (relationship): Связь с распространителем.
        usages (relationship): Связь с использованиями промокода.
    """
    __tablename__ = 'promo_codes'
    id = Column(id_column_type(), primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)
    distributor_id = Column(id_column_type(), ForeignKey('distributors.id'), nullable=False, index=True)
    distributor = relationship('Distributor', back_populates='promo_codes')
    usages = relationship('UserPromoCodeUsage', back_populates='promo_code')

    @staticmethod
    async def find_by_code(session, code: str) -> int:
        """
        Находит промокод по его коду.

        Args:
            session (AsyncSession): Сессия базы данных.
            code (str): Код промокода.

        Returns:
            int: Идентификатор промокода или None, если промокод не найден.
        """
        query = select(PromoCode.id).where(PromoCode.code == code)
        result = await session.execute(query)
        promo_code_id = result.scalar_one_or_none()
        return promo_code_id
    
    @staticmethod
    async def find_by_code_distrib(session, distributor_id: int):
        promo_code_query = select(PromoCode.id).where(PromoCode.distributor_id == distributor_id)
        promo_code_id_result = await session.execute(promo_code_query)
        promo_code_id = promo_code_id_result.scalars().first()
        return promo_code_id
        

class UserPromoCodeUsage(Base):
    """
    Модель использования промокода пользователем.

    Attributes:
        id (int): Уникальный идентификатор использования.
        user_id (int): Идентификатор пользователя, использовавшего промокод.
        promo_code_id (int): Идентификатор промокода.
        usage_date (DateTime): Дата и время использования промокода.
        promo_code (relationship): Связь с промокодом.
    """
    __tablename__ = 'user_promo_code_usages'
    id = Column(id_column_type(), primary_key=True, autoincrement=True)
    user_id = Column(id_column_type(), ForeignKey('users.id'), nullable=False)
    promo_code_id = Column(id_column_type(), ForeignKey('promo_codes.id'), nullable=False)
    usage_date = Column(DateTime, default=func.now())
    promo_code = relationship('PromoCode', back_populates='usages')

    @staticmethod
    async def count_referrals_for_distributor(session: AsyncSession, distributor_id: int):
        """
        Считает количество уникальных пользователей, которых пригласил конкретный Distributor по его id.

        Args:
            session (AsyncSession): Сессия базы данных.
            distributor_id (int): Идентификатор распространителя.

        Returns:
            int: Количество уникальных пользователей, которых пригласил данный распространитель.
        """
        query = (
            select(UserPromoCodeUsage.user_id)
            .join(PromoCode, UserPromoCodeUsage.promo_code_id == PromoCode.id)
            .where(PromoCode.distributor_id == distributor_id)
            .distinct()
        )
        result = await session.execute(query)
        unique_user_ids = result.scalars().all()
        return len(unique_user_ids)
        

    

class UserRequest(Base):
    """
    Модель запроса пользователя.

    Attributes:
        id (int): Уникальный идентификатор запроса.
        user_id (int): Идентификатор пользователя, создавшего запрос.
        direction (str): Направление запроса.
        description (Text): Описание запроса.
        file_id (str): Идентификатор файла, прикрепленного к запросу.
        request_date (DateTime): Дата и время создания запроса.
        status (str): Статус запроса.
    """
    __tablename__ = 'user_requests'
    id = Column(id_column_type(), primary_key=True, autoincrement=True)
    user_id = Column(id_column_type(), ForeignKey('users.id'), nullable=False, index=True)
    direction = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    file_id  = Column(String, nullable=True)
    request_date = Column(DateTime, default=func.now())
    status = Column(String, nullable=False, default="В обработке")

    @staticmethod
    async def get_by_id(session, request_id):
        """
        Получает запрос по его идентификатору.

        Args:
            session (AsyncSession): Сессия базы данных.
            request_id (int): Идентификатор запроса.

        Returns:
            UserRequest: Объект запроса или None, если запрос не найден.
        """
        query = select(UserRequest).where(UserRequest.id == request_id)
        result = await session.execute(query)
        await session.flush()
        return result.scalars().first()
    
    @staticmethod
    async def update_by_id(session, request_id, user_id, **kwargs):
        """
        Обновляет информацию о запросе по его идентификатору.

        Args:
            session (AsyncSession): Сессия базы данных.
            request_id (int): Идентификатор запроса.
            **kwargs
        """
        # Получаем текущий статус перед обновлением
        current_status_query = select(UserRequest.status).where(UserRequest.id == request_id)
        current_status_result = await session.execute(current_status_query)
        current_status = current_status_result.scalar()

        # Выполняем обновление
        query = update(UserRequest).where(UserRequest.id == request_id).values(**kwargs)
        await session.execute(query)
        await session.flush()

        # Логирование изменений
        new_status = kwargs.get('status')
        changes = {'status': {'old': current_status, 'new': new_status}, "user": user_id}
        await AuditLog.log_update(session, 'user_requests', request_id, changes)
    
    @staticmethod
    async def get_distributor_for_request(session, request_id):
        request = await UserRequest.get_by_id(session, request_id)
        logger.info(request)
        if not request:
            return None
        usage = await session.execute(select(UserPromoCodeUsage).where(UserPromoCodeUsage.user_id == request.user_id))
        usage = usage.scalars().first()
        logger.info(usage)
        if not usage:
            return None
        promo_code = await session.execute(select(PromoCode).where(PromoCode.id == usage.promo_code_id))
        promo_code = promo_code.scalars().first()
        logger.info(promo_code)
        if not promo_code:
            return None
        distributor = await session.execute(select(Distributor).where(Distributor.id == promo_code.distributor_id))
        distributor = distributor.scalars().first()
        logger.info(distributor)
        if not distributor:
            return None
        user = await Distributor.get_user_for_distributor(session, distributor.id)
        logger.info(user)
        return user
    
    @staticmethod
    async def find_requests_all(session, user_id: int, page: int, order_type: str = ""):
        offset = (page - 1) * 1
        if order_type != "":
            query = (
                select(UserRequest)
                .where(UserRequest.status == order_type)
                .order_by(
                    case(
                        (UserRequest.file_id != None, 1),
                        else_=2
                    ),
                    UserRequest.request_date.desc()
                )
                .offset(offset)
                .limit(1)
            )
        else:
            query = (
                select(UserRequest)
                .where(and_(UserRequest.user_id == user_id))
                .order_by(
                    case(
                        (UserRequest.file_id != None, 1),
                        else_=2
                    ),
                    UserRequest.request_date.desc()
                )
                .offset(offset)
                .limit(1)
            )
        result = await session.execute(query)
        request = result.scalars().first()
        return request

class Transaction(Base):
    """
    Модель транзакции.

    Attributes:
        id (int): Уникальный идентификатор транзакции.
        distributor_id (int): Идентификатор распространителя, связанного с транзакцией.
        amount (float): Сумма транзакции.
        transaction_date (DateTime): Дата и время совершения транзакции.
        comment (Text): Комментарий к транзакции.
    """
    __tablename__ = 'transactions'
    id = Column(id_column_type(), primary_key=True, autoincrement=True)
    distributor_id = Column(id_column_type(), ForeignKey('distributors.id'), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    transaction_date = Column(DateTime, default=func.now())
    comment = Column(Text, nullable=True)

    @staticmethod
    async def record_transaction(session, distributor_id, amount, comment=None):
        """
        Записывает транзакцию в базу данных.

        Args:
            session (AsyncSession): Сессия базы данных.
            distributor_id (int): Идентификатор распространителя.
            amount (float): Сумма транзакции.
            comment (str, optional): Комментарий к транзакции.
        """
        transaction = Transaction(distributor_id=distributor_id, amount=amount, comment=comment)
        session.add(transaction)
        await session.flush()

class Review(Base):
    """
    Модель отзыва.

    Attributes:
        id (int): Уникальный идентификатор отзыва.
        user_id (int): Идентификатор пользователя, оставившего отзыв.
        review_text (Text): Текст отзыва.
        review_date (DateTime): Дата и время создания отзыва.
        rating (int): Рейтинг отзыва (от 1 до 5).
        user (relationship): Связь с пользователем, оставившим отзыв.
    """
    __tablename__ = 'reviews'
    id = Column(id_column_type(), primary_key=True, autoincrement=True)
    user_id = Column(id_column_type(), ForeignKey('users.id'), nullable=False, index=True)
    title = Column(Text, nullable=False)
    review_text = Column(Text, nullable=False)
    review_date = Column(DateTime, default=func.now())
    rating = Column(Integer, nullable=False)
    vision_review = Column(Boolean, nullable=False, index=True)

    user = relationship('User')

    @validates('rating')
    def validate_rating(self, key, value):
        """
        Проверяет, что рейтинг находится в диапазоне от 1 до 5.

        Args:
            key (str): Ключ атрибута.
            value (int): Значение рейтинга.

        Raises:
            ValueError: Если рейтинг не находится в диапазоне от 1 до 5.

        Returns:
            int: Значение рейтинга.
        """
        if not (1 <= value <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return value

    @staticmethod
    async def add_review(session, user_id: int, title: str, review_text: str, rating: int, vision_review: bool):
        """
        Добавляет отзыв в базу данных.

        Args:
            session (AsyncSession): Сессия базы данных.
            user_id (int): Идентификатор пользователя.
            review_text (str): Текст отзыва.
            rating (int): Рейтинг отзыва.
        """
        review = Review(user_id=user_id, review_text=review_text, rating=rating, title=title, vision_review=vision_review)
        session.add(review)

    @staticmethod
    async def get_reviews_paginated(session, page=1, per_page=1, what_reviews: list[str, int]=["all", 1]) -> tuple['Review', User]:
        """
        Получает отзывы постранично.

        Args:
            session (AsyncSession): Сессия базы данных.
            page (int): Номер страницы.
            per_page (int): Количество отзывов на странице.

        Returns:
            list: Список отзывов для текущей страницы.
        """
        offset = (page - 1) * per_page
        if what_reviews[0] == "all":
            query = select(Review).order_by(Review.review_date.desc()).offset(offset).limit(per_page)
            result = await session.execute(query)
            review: Review = result.scalars().first()
            if review is None:
                return None, None
            query = select(User).where(User.id==review.user_id)
            result = await session.execute(query)
            user_review: User = result.scalars().first()
            return review, user_review
        else:
            user: User = await User.find_user_by_telegram_id(session, what_reviews[1])
            query = select(Review).where(Review.user_id==user.id).order_by(Review.review_date.desc()).offset(offset).limit(per_page)
            result = await session.execute(query)
            review: Review = result.scalars().first()
            return review
        

class AuditLog(Base):
    """
    Модель аудитного лога.

    Attributes:
        id (int): Уникальный идентификатор лога.
        table_name (str): Имя таблицы, к которой относится лог.
        record_id (int): Идентификатор записи в таблице.
        action (str): Действие, совершенное над записью.
        changes (Text): Изменения, внесенные в запись.
        timestamp (DateTime): Дата и время совершения действия.
    """
    __tablename__ = 'audit_logs'
    id = Column(id_column_type(), primary_key=True, autoincrement=True)
    table_name = Column(String, nullable=False)
    record_id = Column(id_column_type(), nullable=False)
    action = Column(String, nullable=False)
    changes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=func.now())

    @staticmethod
    async def log_update(session: AsyncSession, table_name: str, record_id: int, changes: dict):
        log = {
            'table_name': table_name,
            'record_id': record_id,
            'action': 'update',
            'changes': json.dumps(changes, ensure_ascii=False),
            'timestamp': func.now()
        }
        await session.execute(AuditLog.__table__.insert().values(log))
        await session.flush()

@event.listens_for(User, 'after_insert')
def receive_after_insert(mapper, connection, target):
    """
    Обрабатывает событие после вставки новой записи в таблицу пользователей.

    Args:
        mapper: Маппер объекта.
        connection: Соединение с базой данных.
        target: Объект, над которым было совершено действие.
    """
    log = {
        'table_name': 'users',
        'record_id': target.id,
        'action': 'insert',
        'changes': None,
        'timestamp': func.now()
    }
    connection.execute(AuditLog.__table__.insert().values(log))

@event.listens_for(Distributor, 'before_update')
def receive_before_update(mapper, connection, target):
    """
    Обрабатывает событие перед обновлением записи в таблице Distributor.

    Args:
        mapper: Маппер объекта.
        connection: Соединение с базой данных.
        target: Объект, над которым будет совершено действие.
    """
    state = inspect(target)
    
    changes = {}
    for attr_name in state.attrs.keys():
        history = state.get_history(attr_name, True)
        if history.has_changes():
            old_value = history.deleted[0] if history.deleted else None
            new_value = history.added[0] if history.added else None
            changes[attr_name] = {'old': old_value, 'new': new_value}
    
    if changes:
        log = {
            'table_name': 'distributors',
            'record_id': target.id,
            'action': 'update',
            'changes': json.dumps(changes),
            'timestamp': func.now()
        }
        connection.execute(AuditLog.__table__.insert().values(log))
