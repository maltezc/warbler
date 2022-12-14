"""SQLAlchemy models for Warbler."""

from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()
# db = SQLAlchemy(SQLALCHEMY_URI, app=app, record_queries=True)

DEFAULT_IMAGE_URL = "/static/images/default-pic.png"
DEFAULT_HEADER_IMAGE_URL = "/static/images/warbler-hero.jpg"


class Follows(db.Model):
    """Connection of a follower <-> followed_user."""

    __tablename__ = 'follows'

    # recursive relationship
    user_being_followed_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

    user_following_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )



class Like(db.Model):
    """ A liked warble. """

    __tablename__ = 'likes'

    __table_args__ = (
        db.UniqueConstraint(
            'user_id',
            'message_id',
            ),
        )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        # primary_key=True,
    )

    message_id = db.Column(
        db.Integer,
        db.ForeignKey('messages.id', ondelete='CASCADE'),
        nullable=False,
        # primary_key=True,
    )


    # user = db.relationship('User', backref="likes")
    # message = db.relationship('Message', backref="likes")


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    image_url = db.Column(
        db.Text,
        default=DEFAULT_IMAGE_URL,
    )

    header_image_url = db.Column(
        db.Text,
        default=DEFAULT_HEADER_IMAGE_URL,
    )

    bio = db.Column(
        db.Text,
    )

    location = db.Column(
        db.Text,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    # the instance sbeing returned will always be what I passed in
    # as my first arg (Message)
    messages = db.relationship('Message', backref="user")

    # we have two fk that link back to user
    # which column are we linking to?
        # thats why we use primary and secondary join

    # user = 301

    # user.followers
    # SELECT * FROM users WHERE users.id = 301;

    # user.following
    # SELECT * FROM follows WHERE user_following_id = 301;
    # backref looking at secondary join

    followers = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follows.user_being_followed_id == id),
        secondaryjoin=(Follows.user_following_id == id),
        backref="following",
    )

    """
    Secondary:
        every use can make multiple messages 1 to M
        this means I can create a join
        I dont want to know all the messages the user created
        I want to know all the messages the user liked

        Like model
            purpose: keep track user that liked message
                which user liked which msg


        secondary:
            Because the first param is Message, this means what
            are the instances that will be assigned to the variable.

            liked_messages will always be a list of Messages


    Primary join:

    Secondary join:
    """

    # my instances will be messages, but I want those instances
    # coming from the likes table

    # this will only work if likes has a fk that matches
    # the current model we're talking about

    # my Like has the user

    liked_messages = db.relationship(
        "Message",
        secondary="likes",
        # primaryjoin=(Like.user_id == id),
        # secondaryjoin=(Like.message_id == id),
        # backref="user"
    )

    # user.id | user_thatliked_id | message_id


    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def signup(cls, username, email, password, image_url=DEFAULT_IMAGE_URL):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If this can't find matching user (or if password is wrong), returns
        False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

    def is_followed_by(self, other_user): # TODO: CAN WE USE THIS IN OUR SQL-ALCHEMY FILTERS SOME HOW?
        """Is this user followed by `other_user`?"""

        found_user_list = [
            user for user in self.followers if user == other_user]
        return len(found_user_list) == 1

    def is_following(self, other_user):
        """Is this user following `other_use`?"""

        found_user_list = [
            user for user in self.following if user == other_user]
        return len(found_user_list) == 1


class Message(db.Model):
    """An individual message ("warble")."""

    __tablename__ = 'messages'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    text = db.Column(
        db.String(140),
        nullable=False,
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    # def is_liked(self, user):
    #     self in g.user.liked_messages
    #     return t f

    def serialize(self):
        """ Serialize message instance to python dictionary """

        return {
            "id": self.id,
            "text": self.text,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
        }








def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    app.app_context().push()
    db.app = app
    db.init_app(app)
