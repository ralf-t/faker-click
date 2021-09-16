from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

import click
import random
from datetime import datetime
from faker import Faker

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# TABLES ##################################################################################
user_interests = db.Table('user_interests',
                db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                db.Column('topic_id', db.Integer, db.ForeignKey('topic.id'))
            )

saves = db.Table('saves',
        db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
        db.Column('post_id', db.Integer, db.ForeignKey('post.id'))
        )

topics = db.Table('topics',
        db.Column('topic_id', db.Integer, db.ForeignKey('topic.id')),
        db.Column('post_id', db.Integer, db.ForeignKey('post.id'))
        )

class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        first_name = db.Column(db.String(20), nullable=False)
        last_name = db.Column(db.String(20), nullable=False)
        username = db.Column(db.String(20), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password = db.Column(db.String(60), nullable=False)
        profile_picture = db.Column(db.String(20), nullable=False, default='default.jpg')
        

        # adds an 'invisible column' to Topic table named interested_user
        # which can be used to see user details that is interested in that topic ex.
        # for user in topic1.interested_user:
        #   print(user.username)
        topics_of_interest = db.relationship('Topic', secondary=user_interests,
                            backref=db.backref('interested_user'), lazy='dynamic')

        saved_posts = db.relationship('Post', secondary=saves,
                            backref=db.backref('saved_by'), lazy='dynamic')

        authored_posts = db.relationship('Post', backref='author', lazy=True)

        def __repr__(self):     #what will be printed out when we print this model
            return f"User('{self.first_name} {self.last_name}', '{self.username}', '{self.email}', '{self.profile_picture}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    #use the author attribute to access post author details

    def __repr__(self):
        return f"Post('{self.title}', '{self.created_at}')"

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(30), nullable=False)
    posts = db.relationship('Post', secondary=topics,
                            backref=db.backref('topic'), lazy='dynamic')

    def __repr__(self):
        return f"Topic('{self.id}', '{self.topic}')"


# Setup and teardown ######################################################################
@app.cli.command("setup-db")
def setup_db():
    # all necessary db and models must be imported

    choice = input("This will delete any existing database and rebuild from scratch. Press \"y\" to proceed. : ").lower()
    
    if choice == 'y':
        db.drop_all()
        print("DB dropped.")

        print("Creating DB...")
        db.create_all()

        print("Creating topics...")

        # create topics
        for i in range(10):
            # localize to lorem
            fake = Faker("la")
            
            topic = Topic()
            topic.topic = fake.word()
            
            db.session.add(topic)
            
        db.session.commit()

        # topics query
        topics = Topic.query.all()

        # create 5 user and their posts(with topics)
        print("Creating user and posts...")

        for i in range(5):
            fake = Faker()
            
            user = User()
            user.first_name = fake.first_name()
            user.last_name = fake.last_name()
            user.username = fake.user_name()
            user.email = fake.email()
            user.password = bcrypt.generate_password_hash("secret").decode("utf-8")

            # 2-5 posts for each user
            for i in range(random.randint(2,5)):
                # localize to lorem
                fake = Faker("la")

                post = Post()
                post.title = fake.paragraph(nb_sentences=2, variable_nb_sentences=True)
                post.content = fake.paragraph(nb_sentences=10, variable_nb_sentences=True)
                post.author = user

                # post will have 1-5 topics
                for j in range(random.randint(1,5)):
                    # get a random topic
                    random_topic = lambda : topics[random.randint(0, len(topics) - 1)]
                    
                    post.topic.append(random_topic())
                
                db.session.add(post)
            
            # user will have 3-5 topics of interest
            for i in range(random.randint(3,5)):
                user.topics_of_interest.append(random_topic())

        # commit here now to query users later
        db.session.commit()
        
        # posts query
        posts = Post.query.all()
        random_post = lambda : posts[random.randint(0, len(posts) - 1)]
        
        # save 2-5 posts
        for u in User.query.all():
            # can also save own post
            for i in range(random.randint(2,5)):
                u.saved_posts.append(random_post())
        
        # admin
        user = User()
        user.first_name = "admin"
        user.last_name = "admin"
        user.username = "admin"
        user.email = "admin@admin.com"
        user.password = bcrypt.generate_password_hash("secret").decode("utf-8")

        db.session.add(user)

        # final commit
        db.session.commit()

        print("Done!")

    else:
        print("DB setup aborted!")

@app.cli.command("teardown-db")
def teardown_db():
    try:
        # will return error if db is not created yet or if there is a missing table
        User.query.all()
        Post.query.all()
        Topic.query.all()
        
        db.drop_all()

        click.echo("Database has been dropped.")

    except:
        click.echo("Database and tables might have been altered manually. If error persists, delete the database manually.")
        

# app loop
if __name__ == "__main__":
    app.run(debug=True)