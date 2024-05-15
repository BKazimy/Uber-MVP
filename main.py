from flask_bootstrap import Bootstrap5
from datetime import datetime


import flask
import sqlalchemy
import flask_sqlalchemy
import flask_wtf
import wtforms


app = flask.Flask(__name__)
app.config['SECRET_KEY'] = "asdfaEEFwEFwe3@23WEF$rEWE"
Bootstrap5(app)


class Base(sqlalchemy.orm.DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///boobar.db"
db = flask_sqlalchemy.SQLAlchemy(model_class=Base)
db.init_app(app)


class Rides(db.Model):
    __tablename__ = 'rides'
    id = sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True)
    depart = sqlalchemy.Column('depart', sqlalchemy.String)
    target = sqlalchemy.Column('target', sqlalchemy.String)
    distance = sqlalchemy.Column('distance', sqlalchemy.FLOAT)
    
    est_time = sqlalchemy.Column('est_time', sqlalchemy.Integer, nullable=True)
    cmp_time = sqlalchemy.Column('cmp_time', sqlalchemy.Integer, nullable=True)
    state = sqlalchemy.Column('state', sqlalchemy.String)
    est_fare = sqlalchemy.Column('est_fare', sqlalchemy.Integer)
    real_fare = sqlalchemy.Column('real_fare', sqlalchemy.Integer, nullable=True)
    post_time = sqlalchemy.Column('post_time', sqlalchemy.Integer)
    state_updt_time = sqlalchemy.Column('Update_time', sqlalchemy.Integer)


with app.app_context():
    db.create_all()


class PostRide(flask_wtf.FlaskForm):
    depart = wtforms.StringField("From", validators=[wtforms.validators.DataRequired()])
    target = wtforms.StringField("To", validators=[wtforms.validators.DataRequired()])
    distance = wtforms.FloatField("Distance (km)", validators=[wtforms.validators.DataRequired()])
    est_time = wtforms.IntegerField("Estimated time (minutes)", validators=[wtforms.validators.DataRequired()])
    submit = wtforms.SubmitField("Post")


@app.route('/')
def home():
    return flask.render_template("index.html")


@app.route('/rider', methods=['get', 'post'])
def rider():
    form = PostRide()
    
    if flask.request.method == "POST":
        form.validate()
        print(form.data)
        est_time = form.est_time.data
        dist = form.distance.data
        est_fare = fare_calculator(dist, est_time)
        
        db.session.add(Rides(
            depart=form.depart.data,
            target=form.target.data,
            distance=dist,
            est_time=est_time,
            cmp_time=est_time,
            state="waiting",
            est_fare=est_fare,
            real_fare=est_fare,
            post_time=int(datetime.now().timestamp())
        ))
        db.session.commit()
        flask.flash('Ride posted!', 'success')
        return flask.redirect(flask.url_for('rider'))
        
    rides = db.session.execute(sqlalchemy.select(Rides).filter(Rides.state=='waiting').order_by(Rides.id.desc())).scalars()
    cmp_ride = db.session.execute(sqlalchemy.select(Rides).filter(Rides.state=='completed').order_by(Rides.id.desc())).scalars()
    crnt_ride = db.session.execute(sqlalchemy.select(Rides).filter(Rides.state=='prosessing').order_by(Rides.state_updt_time.desc())).scalars()
        
    return flask.render_template('rider.html', form=form, rides=rides, crnt_ride=crnt_ride, cmp_ride=cmp_ride)


@app.route('/driver')
def driver():
    waiting_posts = db.session.execute(sqlalchemy.select(Rides).filter(Rides.state=='waiting').order_by(Rides.id.desc())).scalars()
    processing_posts = db.session.execute(sqlalchemy.select(Rides).filter(Rides.state=='prosessing').order_by(Rides.id.desc())).scalars()
    completed_posts = db.session.execute(sqlalchemy.select(Rides).filter(Rides.state=='completed').order_by(Rides.id.desc())).scalars()
    return flask.render_template('driver.html', waiting_posts=waiting_posts, processing_posts=processing_posts, completed_posts=completed_posts)


@app.route('/cancel/<id>')
def cancel(id):
    ride = db.get_or_404(Rides, id)
    ride.state = 'canseled'
    ride.state_updt_time=int(datetime.now().timestamp())
    db.session.commit()
    flask.flash('Ride cancelled!', 'success')
    return flask.redirect(flask.url_for('rider'))


@app.route('/confirm/<id>')
def confirm(id):
    ride = db.get_or_404(Rides, id)
    ride.state = 'prosessing'
    ride.state_updt_time=int(datetime.now().timestamp())
    db.session.commit()
    flask.flash('Ride is under process.', 'success')
    return flask.redirect(flask.url_for('driver'))


@app.route('/complet/<id>')
def complet(id):
    ride = db.get_or_404(Rides, id)
    ride.state = 'completed'
    ride.cmp_time = int((datetime.now().timestamp() - ride.state_updt_time) / 60)
    ride.state_updt_time=int(datetime.now().timestamp())
    ride.real_fare=fare_calculator(ride.distance, ride.cmp_time)
    db.session.commit()
    flask.flash('Ride is completed.', 'success')
    return flask.redirect(flask.url_for('driver'))


def fare_calculator(dist, min):
    return int((dist * 6) + (min * 1.5) + 25)


if __name__=="__main__":
    app.run(debug=True)