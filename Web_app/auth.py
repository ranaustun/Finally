import os.path
from datetime import datetime, date

import stripe

from . import mail, create_app
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, session as s, session
from flask_mail import Message

from . import db, models
from .models import User, Studio, Reservations, Userstudio, Pictures
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)


@auth.route('/signup', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        name_surname = request.form.get('name_Surname').strip()
        email = request.form.get('email').strip()
        password1 = request.form.get('password1').strip()
        password2 = request.form.get('password2').strip()

        user = User.query.filter_by(email=email).first()

        if user:
            flash('Email already exist!', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 4 characters.', category='error')
        elif len(name_surname) < 1:
            flash('Name must be greater than 2 characters.', category='error')
        elif len(password1) < 8:
            flash('Password must at least 8 characters.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match .', category='error')
        else:
            new_user = User(name_surname=name_surname, email=email,
                            password=generate_password_hash(password1, method='sha256'))
            db.session.add(new_user)  # adding the new user to the database
            db.session.commit()

            login_user(new_user, remember=True)

            return redirect(url_for('views.home'))  # redirect the page to the home page

    return render_template("signup.html")


@auth.route('/signin', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again!', category='error')
        else:
            flash('Email does not exist!', category='error')
    return render_template("signin.html")


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/info')
@login_required
def info():
    return render_template("Info.html")


# filtering

@auth.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    studio_f = Studio.query.all()
    country = request.form.get('country')
    if country == "-1":  #value of the country is -1
        country = ""
    city = request.form.get('selectcity')
    if city == "-1":
        city = ""
    studio_type = request.form.get('studio_type')
    if studio_type == "-1":
        studio_type = ""
    if country and studio_type and city:

        studio_f = Studio.query.filter_by(country=country, surface=studio_type, city=city).all()
    elif country and studio_type:
        studio_f = Studio.query.filter_by(country=country, surface=studio_type).all()
    elif city and studio_type:
        studio_f = Studio.query.filter_by(city=city, surface=studio_type).all()
    elif country and city:
        studio_f = Studio.query.filter_by(city=city, country=country).all()
    elif country:
        studio_f = Studio.query.filter_by(country=country).all()
    elif city:
        studio_f = Studio.query.filter_by(city=city).all()
    elif studio_type:
        studio_f = Studio.query.filter_by(surface=studio_type).all()
    elif country == "-1" or city == "-1" or studio_type == "-1":
        studio_f = Studio.query.all()

    elif country or city or studio_type:
        studio_f = Studio.query.filter(
            Studio.country.contains(country) | Studio.city.contains(city) | Studio.surface.contains(studio_type))
    else:
        studio_f = Studio.query.all()

    return render_template('book.html', studio_f=studio_f)


@auth.route('/studio_details/<studio_name>', methods=['GET', 'post'])
@login_required
def studio_details(studio_name):
    studio = Studio.query.filter_by(studio_name=studio_name, active=1).first()
    filename = Pictures.query.filter_by(studio_name=studio_name).all()
    return render_template('studio_details.html', studio=studio, filenames=filename)


@auth.route('/order/<product_id>', methods=['GET', 'POST'])
@login_required
def order(product_id):
    if request.method == 'POST':
        studio = Studio.query.filter_by(id=product_id).first()
        clicked_date = request.form.get('date')
        time = request.form.get('time')
        check_out_time = request.form.get('check_out_time')
        chosen_date = Reservations.query.filter_by(studio_id=product_id, studio_busy_date=clicked_date).first()
        chosen_time = Reservations.query.filter_by(studio_id=product_id, studio_busy_time=time).first()
        chosen_check_out_time = Reservations.query.filter_by(studio_id=product_id, studio_check_out_time=check_out_time)

        if chosen_date:
            if chosen_time:
                flash("Choose Another Time", category='error')
                return redirect(url_for('auth.studio_details',
                                        studio_name=studio.studio_name))
        if clicked_date == '':
            flash("Choose a date", category='error')
        elif datetime.strptime(clicked_date, "%Y-%m-%d") < datetime.now():
            flash("Choose a date in the future", category="error")
        elif time == '':
            flash("Choose a check-in time", category='error')
        elif chosen_check_out_time == '':
            flash("Choose a check-out time", category='error')
        elif check_out_time == time:
            flash("Check out and check in time cannot be the same", category='error')
        elif check_out_time < time:
            flash("Check-out cannot be before the check-in",category='error')
        else:

            converted_check_in_time = convert24(time)
            converted_check_out_time = convert24(check_out_time)
            check_in_time_split = converted_check_in_time.split(":")
            check_out_time_split = converted_check_out_time.split(":")

            check_in_time_hour = check_in_time_split[0]
            check_out_time_hour = check_out_time_split[0]

            price = int(check_out_time_hour) - int(check_in_time_hour)

            session = stripe.checkout.Session.create(

                line_items=[  # specifies the product that the user wishes to purchase.
                    {

                        'price_data': {
                            'product_data': {
                                'name': studio.studio_name,
                            },
                            'unit_amount': studio.price * 100 * price,
                            'currency': 'eur',
                        },
                        'quantity': 1,

                    },
                ],
                metadata={'user_id': current_user.id,
                          'studio_id': studio.id,
                          'user_name': current_user.name_surname,
                          'user_email': current_user.email,
                          'studio_name': studio.studio_name,
                          'date': clicked_date,
                          'time': time,
                          'check_out_time': check_out_time,
                          'price': studio.price * price
                          },
                customer_email=current_user.email,
                payment_method_types=['card'],  # what methods of payment you want to accept.
                mode='payment',
                success_url=request.host_url + 'order/success',
                cancel_url=request.host_url + 'order/cancel',

            )
            return redirect(session.url, code=303)
        return redirect(url_for('auth.studio_details',
                                studio_name=studio.studio_name))


@auth.route('/stripe_webhook', methods=['POST'])
def stripe_webhook():
    global studio_owner_email
    print('WEBHOOK CALLED')

    payload = request.get_data()

    sig_header = request.environ.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = 'whsec_63a3f113f458d3fb7cfb4a43bff6f4a9b8044d883c517e8be723d222d5b57ef4'
    event = None
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        print('INVALID PAYLOAD')
        return {}, 400
    except stripe.error.SignatureVerificationError as e:
        print('INVALID SIGNATURE')
        return {}, 400
    if event['type'] == 'checkout.session.completed':
        if request.method == 'POST':
            request.form.get('date')
            request.form.get('time')
            request.form.get('check_out_time')
            metadata_studio_id = event['data']['object']['metadata']['studio_id']
            metadata_studio_name = event['data']['object']['metadata']['studio_name']
            metadata_user_name = event['data']['object']['metadata']['user_name']
            metadata_user_email = event['data']['object']['metadata']['user_email']
            metadata_user = event['data']['object']['metadata']['user_id']
            metadata_date = event['data']['object']['metadata']['date']
            metadata_time = event['data']['object']['metadata']['time']
            metadata_check_out_time = event['data']['object']['metadata']['check_out_time']
            metadata_price = event['data']['object']['metadata']['price']
            reservations = Reservations(user_id=metadata_user, studio_id=metadata_studio_id,
                                        studio_busy_date=metadata_date,
                                        studio_busy_time=metadata_time,
                                        studio_check_out_time=metadata_check_out_time,
                                        reservation_date=datetime.now(),
                                        active=1)
            db.session.add(reservations)  # adding new reservation to the database
            db.session.commit()
            owner_email = db.engine.execute(
                'Select u.email from user as u left join userstudio us on us.user_id=u.id where us.studio_id=' + metadata_studio_id)
            for row in owner_email:
                studio_owner_email = row["email"]
            msg_client = Message(
                subject='Your reservation has been completed',
                body='Your booking has been completed.\nHi ' + metadata_user_name +
                     ',this email confirms that your studio reservation is finished.'
                     '\nAmount that you paid is €' + metadata_price +
                     '\nWe are really happy to see you, thanks for giving us a try!'
                     '\nIf you have any question do not hesitate and write!'
                     'Our email is ' + studio_owner_email +
                     'We are waiting for you on ' + metadata_date + ',at ' + metadata_time + '. '
                                                                                             '\nThanks again for being our customer.The crew at Superior '
                                                                                             '\nStudio Rent '
                                                                                             'https://studiorenting.azurewebsites.net',
                recipients=[metadata_user_email])
            mail.send(msg_client)
            msg_owner = Message(
                subject='You have a new reservation',
                body='Your studio has been reserved by ' + metadata_user_name +
                     '\nClient email: ' + metadata_user_email +
                     '.\nThe studio: ' + metadata_studio_name +
                     '\nOn: ' + metadata_date + '\nBetween: ' + metadata_time + ' and ' + metadata_check_out_time +
                     '\nThe crew at Superior Studio Renting https://studiorenting.azurewebsites.net',
                recipients=[studio_owner_email])
            mail.send(msg_owner)
    return {}


@auth.route('/order/success')
def success():
    return render_template('success.html')


@auth.route('/mybookings/<user_id>')
def mybookings(user_id):
    reservations_table = db.engine.execute(
        "Select r.reservation_date,r.studio_check_out_time,r.active,r.studio_id, r.studio_busy_date,r.studio_busy_time,s.*,r.id rez_id from reservations as r left join user u on u.id=r.user_id left join studio s on s.id=r.studio_id where r.active=1 and r.user_id=" + user_id)
    filename = Pictures.query.filter(Pictures.user_id == user_id).all()
    return render_template('mybookings.html', reservations=reservations_table, filenames=filename)


@auth.route('/cancel_reservation/<id>')
def delete_reservation(id):
    global client_name_surname, busy_date, busy_time, check_out_time, studio_owner_email, studio_name
    reservation_to_delete = Reservations.query.filter_by(id=id).first()

    if reservation_to_delete:
        reservation_to_delete.active = 0
        db.session.commit()
        print("Reservation is deleted")
        print(id)
        msg = Message(
            subject='Your reservation has been canceled',
            body='Your booking has been canceled.\nHi ' + current_user.name_surname +
                 ',this email confirms that your studio reservation has been canceled.'
                 '\nWe are really sorry to see you go, but thanks for giving us a try.!If you believe this '
                 'cancellation is in error, or you have any other questions '
                 'about your reservation, please write back.'
                 '\nThanks again for being our customer.'
                 'The crew at Superior Studio Renting https://studiorenting.azurewebsites.net'
            ,
            recipients=[current_user.email])
        mail.send(msg)
        information = db.engine.execute(
            "Select u.name_surname, r.studio_busy_date,r.studio_busy_time, r.studio_check_out_time from user as u "
            "left join reservations r on r.user_id=u.id where r.id=" + id)

        for row in information:
            client_name_surname = row["name_surname"]
            busy_date = row["studio_busy_date"]
            busy_time = row["studio_busy_time"]
            check_out_time = row["studio_check_out_time"]
        owner_email = db.engine.execute(
            'Select us.user_id, u.name_surname,u.email,s.studio_name from userstudio as us left join reservations '
            'r on us.studio_id=r.studio_id left join user as u left join studio as s on us.studio_id=s.id where '
            'r.id=' + id + ' and u.id=us.user_id')
        for row2 in owner_email:
            studio_owner_email = row2["email"]
            studio_name = row2['studio_name']
        msg_to_owner = Message(subject='Your client canceled a reservation',
                               body='Unfortunately your client: ' + client_name_surname + ' has canceled a '
                                                                                          'reservation, of studio:' + studio_name + ' which was on ' + busy_date + ' between ' + busy_time + ' and ' + check_out_time,
                               recipients=[studio_owner_email])
        mail.send(msg_to_owner)
    else:
        print("Reservation is not deleted")
    return render_template('home.html')


@auth.route('/order/cancel')
def cancel():
    return render_template('cancel.html')


@auth.route('/mystudios/<name_surname>')
@login_required
def mystudios(name_surname):
    studios = Studio.query.filter(Studio.studio_owner == name_surname)
    return render_template('mystudios.html', studios=studios)


@auth.route('/new_studio', methods=['POST', 'GET'])
@login_required
def new_studio():
    global new_studio_add
    if request.method == 'POST':
        studio_name = request.form.get('studio_name').strip()
        surface = request.form.get('surface')
        description = request.form.get('description')
        country = request.form.get('country')
        city = request.form.get('selectcity')
        address = request.form.get('street')
        price = request.form.get('price').strip()
        pictures = request.files.getlist('image')
        iban = request.form.get('iban')
        studio_owner = current_user.name_surname

        studio = Studio.query.filter_by(studio_name=studio_name).first()

        if studio is None:
            if studio_name == '':
                flash('Give a  name', category='error')
            elif '\'' in studio_name:
                flash("Give a proper name", category='error')
            elif surface == '':
                flash('Choose a surface for your studio', category='error')
            elif description == '':
                flash('Describe your studio.', category='error')
            elif country == '':
                flash('Choose a country .', category='error')
            elif city == '':
                flash("Select a city", category='error')
            elif address == '':
                flash("Input an address", category='error')
            elif price == '':
                flash("Give a price", category='error')
            elif studio_name and description and country and city and address and surface and price is None:
                flash("Fill in the blanks", category="error")
            elif not pictures:
                flash("Upload at least one photo of your studio")
            elif not iban:
                flash("Fill in the blank", category="error")
            else:

                new_studio_add = Studio(studio_name=studio_name, studio_owner=studio_owner, description=description,
                                        country=country, city=city, street=address, surface=surface,
                                        price=price, active=1)
                db.session.add(new_studio_add)
                db.session.commit()
                user = User.query.filter_by(
                    name_surname=studio_owner).first()
                user.iban = iban
                db.session.commit()
                user_studio = Userstudio(studio_id=new_studio_add.id,
                                         user_id=current_user.id)

                db.session.add(user_studio)  # adding the new reservation to the database
                db.session.commit()
                image_names = []
                for image in pictures:
                    if image:
                        filename = secure_filename(image.filename)
                        image_names.append(filename)
                        image.save(os.path.join(create_app().root_path, 'static/studios', filename))
                        new_picture = Pictures(user_id=current_user.id, studio_name=studio_name,
                                               studio_id=new_studio_add.id, pictures=filename)
                        db.session.add(new_picture)
                        db.session.commit()
                        session['filename'] = filename

                return redirect(url_for('auth.mystudios',
                                        name_surname=current_user.name_surname, images=image_names))
        elif studio.active == 1:
            flash("This name of studio is already exist!", category='error')
        else:
            new_studio_add = Studio(studio_name=studio_name, studio_owner=studio_owner, description=description,
                                    country=country, city=city, street=address, surface=surface,
                                    price=price, active=1)
            db.session.add(new_studio_add)
            db.session.commit()
            user = User.query.filter_by(
                name_surname=studio_owner).first()
            user.iban = iban
            db.session.commit()
            user_studio = Userstudio(studio_id=new_studio_add.id,
                                     user_id=current_user.id)

            db.session.add(user_studio)  # adding the new reservation to the database
            db.session.commit()
            image_names = []
            for image in pictures:
                if image:
                    filename = secure_filename(image.filename)
                    image_names.append(filename)
                    image.save(os.path.join(create_app().root_path, 'static/studios', filename))

                    new_picture = Pictures(user_id=current_user.id, studio_name=studio_name,
                                           studio_id=new_studio_add.id, pictures=filename)
                    db.session.add(new_picture)
                    db.session.commit()
                    session['filename'] = filename

            return redirect(url_for('auth.mystudios',
                                    name_surname=current_user.name_surname, images=image_names))

        return render_template("new_studio.html")
    return render_template("new_studio.html")


@auth.route('/studio_edit/<studio_name_e>', methods=['GET', 'POST'])
@login_required
def studio_edit(studio_name_e):
    studios = Studio.query.filter(Studio.studio_name == studio_name_e).all()
    filename = Pictures.query.filter(Pictures.studio_name == studio_name_e).all()
    if request.method == 'POST':
        studio_name = request.form.get('studio_name')
        surface = request.form.get('surface')
        description = request.form.get('description')
        country = request.form.get('country')
        city = request.form.get('selectcity')
        address = request.form.get('street')
        price = request.form.get('price')
        studio_owner = current_user.name_surname
        pictures = request.files.getlist('image')

        studio = Studio.query.filter_by(studio_name=studio_name).first()
        if surface == '' or surface is None:
            flash('Choose a surface for your studio', category='error')
        elif description == '':
            flash('Describe your studio.', category='error')
        elif country == '' or country is None:
            flash('Choose a country .', category='error')
        elif city == '' or city is None:
            flash("Select a city", category='error')
        elif address == '':
            flash("Input an address", category='error')
        elif price == '':
            flash("Give a price", category='error')
        elif studio_name and description and country and city and address and surface and price is None:
            flash("Fill in the blanks", category="error")
        else:

            studio.studio_name = studio_name
            studio.studio_owner = studio_owner
            studio.description = description
            studio.country = country
            studio.city = city
            studio.street = address
            studio.surface = surface
            studio.price = price
            current_user.studio_id = studio_name

            image_names = []
            for image in pictures:
                if image:
                    filename = secure_filename(image.filename)
                    image_names.append(filename)
                    image.save(os.path.join(create_app().root_path, 'static/studios', filename))
                    new_picture = Pictures(user_id=current_user.id, studio_name=studio_name,
                                           studio_id=studio.id, pictures=filename)
                    db.session.add(new_picture)
                    db.session.commit()
            return redirect(
                url_for('auth.studio_edit', studio_name_e=studio_name,
                        filenames=filename))  # redirect the page to the new studio page

    if request.method == 'GET':
        return render_template("studio_edit.html", studios=studios,
                               filenames=filename)

    return render_template("studio_edit.html", studios=studios, filenames=filename)


@auth.route('/delete_studio/<studio_id>', methods=['GET', 'POST'])
@login_required
def delete_studio(studio_id):
    studio_to_delete = Studio.query.filter_by(id=studio_id).first()
    reservation_delete = Reservations.query.filter_by(studio_id=studio_id).first()
    if studio_to_delete:
        if reservation_delete:
            if reservation_delete.active == 1:
                flash("You can not delete your studio because you have already got a reservation on it",
                      category='error')
            else:
                studio_to_delete.active = 0
                Pictures.query.filter_by(studio_id=studio_id).delete()

                db.session.commit()
                #print("Studio is deleted")

        else:
            studio_to_delete.active = 0
            picture_to_delete = Pictures.query.filter_by(studio_id=studio_id).first()
            db.session.delete(picture_to_delete)
            db.session.commit()
           # print("Studio is deleted")
            return render_template("mystudios.html", autoflush=False)
    else:
        print("Studio is not deleted")
    return render_template("mystudios.html")


# Account.html -> changing data
@auth.route('/account', methods=['GET', 'POST'])
@login_required
def save_changes():
    account = "account.html"

    if request.method == 'POST':
        name_surname = request.form.get('c_name_surname')
        email = request.form.get('c_email')
        address = request.form.get('address')
        country = request.form.get('country')
        postalcode = request.form.get('postalcode')
        user = User.query.filter_by(
            email=email).first()
        user.name_surname = name_surname
        user.email = email
        user.address = address
        user.country = country
        user.postalcode = postalcode
        Studio.studio_owner = name_surname

        db.session.commit()
        user = current_user
        #print(email, name_surname, address, country, postalcode, user.name_surname)

        return render_template(account, email=email, name_surname=name_surname, address=address, country=country,
                               postalcode=postalcode)

    return render_template("account.html")

@auth.route('/change_password/<string:name_surname>', methods=['GET', 'POST'])
@login_required
def change_password(name_surname):
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        conf_new_password = request.form.get('conf_new_password')
        user = User.query.filter_by(name_surname=name_surname).first()

        if user:

            if check_password_hash(user.password, old_password):

                if old_password == new_password:
                    flash("The new password can not be the same as old one!", category='error')
                elif new_password != conf_new_password:
                    flash("Confirmation is invalid!")
                else:
                    user.password = generate_password_hash(new_password)

                    db.session.commit()
                    flash("Your password changed Successfully!", category='success')
                    return render_template("change_password.html", password=new_password)
            else:
                flash("Invalid old password", category='error')
        else:
            flash('There is an error', category='error')

    return render_template("change_password.html")


def convert24(str1):
    # Checking if last two elements of time
    # is AM and first two elements are 12
    if str1[-2:] == "AM" and str1[:2] == "12":
        return "00" + str1[2:-2]

    # remove the AM
    elif str1[-2:] == "AM":
        return str1[:-2]

    # Checking if last two elements of time
    # is PM and first two elements are 12
    elif str1[-2:] == "PM" and str1[:2] == "12":
        return str1[:-2]

    else:

        # add 12 to hours and remove PM
        return str(int(str1[:2]) + 12) + str1[2:8]
