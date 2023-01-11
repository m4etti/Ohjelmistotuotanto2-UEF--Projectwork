from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, login_required, logout_user, current_user
from . import db
from .models import Matkaaja, Matkakohde, Matka, Tarina, Kuva
import email
import uuid as uuid
import os
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, current_app
from sqlalchemy import false
views = Blueprint('views', __name__)


@views.route('/')
def koti():
    return render_template("koti.html", user=current_user)

@views.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        #luetaan syätetyt tiedot
        email = request.form.get('email')
        etunimi = request.form.get('etunimi')
        sukunimi = request.form.get('sukunimi')
        nimimerkki = request.form.get('nimimerkki')
        paikkakunta = request.form.get('paikkakunta')
        esittely = request.form.get('esittely')
        salasana1 = request.form.get('salasana1')
        salasana2 = request.form.get('salasana2')
        
        #luetaan tietokannasta jo käytössä olevat spostit ja nimimerkit
        user = Matkaaja.query.filter_by(email=email).first()
        nicname = Matkaaja.query.filter_by(nimimerkki=nimimerkki).first()
        
        #jos syätöissä ongelmia errer visti
        if user:
            flash('Sähköposti on jo käytössä.', category='error')
        elif nicname:
            flash('Nimimerkki on jo käytössä.', category='error')
        elif len(email) < 4:
            flash('Sähköpostin täytyy sisältää yli 3 merkkiä.', category='error')
        elif salasana1 != salasana2:
            flash('Salasanat eivät täsmää.', category='error')
        elif len(salasana1) < 3:
            flash('Salasanan täytyy olla ainakin 3 merkkiä pitkä.', category='error')
        #jos ei tallennetaan tiedot tietokantaan    
        else:
            new_user = Matkaaja(email=email, etunimi=etunimi, sukunimi=sukunimi, nimimerkki=nimimerkki, paikkakunta=paikkakunta, esittely=esittely, password=generate_password_hash(
                salasana1, method='sha256'), kuva="default_user.png")
            db.session.add(new_user)
            db.session.commit()
            #jos rekisteröityminen onnistui kirjataan käyttäjä sisään ja ohjataan etusivulle
            login_user(new_user, remember=False)
            flash('Käyttäjä luotu!', category='success')
            return redirect(url_for('views.koti'))
    return render_template("sign_up.html", user=current_user)

@views.route('/log_in', methods=['GET', 'POST'])
def log_in():
    if request.method == 'POST':
        #luetaan syätetyt tiedot
        email = request.form.get('email')
        password = request.form.get('password')
        user = Matkaaja.query.filter_by(email=email).first()
        # verrataan tietokantaan jos virheitä niin ilmoitus jos ei kirjataan käyttäjä sisään ja ohjataan etusivulle
        if user:
            if check_password_hash(user.password, password):
                flash('Kirjautuminen onnistui!', category='success')
                login_user(user, remember=False)
                return redirect(url_for('views.koti'))
            else:
                flash('Väärä salasana, yritä uudelleen.', category='error')
        else:
            flash('Virheellinen sähköposti.', category='error')
    return render_template("log_in.html", user=current_user)

@views.route('/log_out')
@login_required
def log_out():
    #kirjataan käyttäjä ulos ja ohjataan kotisivulle
    logout_user()
    flash('Käyttäjä kirjattu ulos.', category='success')
    session["viimematka"] = None
    session["viimekohde"] = None
    session["viimematka_porukan"] = None
    return redirect(url_for('views.koti'))

@views.route('/omatmatkat', methods=['GET', 'POST'])
@login_required
def omatmatkat():
    user = current_user
    matkat = db.session.query(Matka).filter_by(idmatkaaja=user.id)
    kohteet = db.session.query(Matkakohde)
    lisaa_matka = False
    paivita_matka = False
    lisaa_tarina = False
    paivita_tarina = None
    #jos ei ole valittuna mitään kohdetta valitaan eka
    if "viimematka" not in session:
        session["viimematka"] = matkat.first().idmatka

    if request.method == "POST":
        # mitä kohdetta klikattiin
        idmatka = request.form.get("matka")
        if idmatka:
            session["viimematka"] = idmatka

        # napien painallukset
        nappi = request.form.get("nappi")
        if nappi == "lisaa_matka":
            lisaa_matka = True

        if nappi == "paivita_matka":
            paivita_matka = True

        elif nappi == "poista_matka":
            poistettava_matka = matkat.filter_by(
                idmatka=session["viimematka"]).first()
            es = session["viimematka"]
            db.session.delete(poistettava_matka)
            db.session.commit()
            # valitaan listan eka kohde
            session["viimematka"] = matkat.first().idmatka

        elif nappi == "tallenna_matka" or nappi == "tallenna_matka_paivita":
            #luetaan syötetyt arvot ja tarkistetaan pvm järjestys
            alkupvm = request.form.get('alkupvm')
            loppupvm = request.form.get('loppupvm')
            alkupvm_value = int(alkupvm.replace("-", ""))
            loppupvm_value =  int(loppupvm.replace("-", ""))
            if loppupvm_value < alkupvm_value:
                flash('Virheelliset päivämäärät.', category='error')
            else:
                yksityinen = request.form.get('yksityinen')
                if yksityinen:
                    yksityinen = True
                else:
                    yksityinen = False
                    #tallennetaan matka tietokantaan
                if nappi == "tallenna_matka":
                    uusimatka = Matka(alkupvm=alkupvm, loppupvm=loppupvm,
                                    yksityinen=yksityinen, idmatkaaja=user.id)
                    db.session.add(uusimatka)
                    db.session.commit()
                    session["viimematka"] = uusimatka.idmatka
                # sama päivitykselle
                else:
                    matka = db.session.query(Matka).filter_by(
                        idmatka=session["viimematka"]).first()
                    matka.alkupvm = alkupvm
                    matka.loppupvm = loppupvm
                    matka.yksityinen = yksityinen
                    db.session.commit()

        elif nappi == "lisaa_tarina":
            lisaa_tarina = True

        #tarinoiden tallennus
        elif nappi and "tallenna_tarina" in nappi:
            pvm = request.form.get('pvm')
            pvm_value = int(pvm.replace("-",""))
            #päivämäärän tarkistus
            alku = int(db.session.query(Matka).get(session["viimematka"]).alkupvm.replace("-",""))
            loppu = int(db.session.query(Matka).get(session["viimematka"]).loppupvm.replace("-",""))
            if pvm_value > loppu or pvm_value < alku:
                flash('Virheellinen päivämäärä.', category='error')
            else:
                kohdenimi = request.form.get('matkakohde')
                teksti = request.form.get('teksti')
                kohde_id = db.session.query(Matkakohde).filter_by(kohdenimi=kohdenimi).first().idmatkakohde
                #tarinan talletus tietokantaan
                if nappi == "tallenna_tarina":
                    uusitarina = Tarina(
                        pvm=pvm, idmatkakohde=kohde_id, teksti=teksti, idmatka=session["viimematka"])
                    db.session.add(uusitarina)
                # sama päivitykselle    
                else:
                    tarina_id = nappi.replace("tallenna_tarina_paivita", "")
                    tarina = db.session.query(Tarina).filter_by(
                        idtarina=tarina_id).first()
                    tarina.pvm = pvm
                    tarina.idmatkakohde = kohde_id
                    tarina.idmatka = session["viimematka"]
                    tarina.teksti = teksti
                    db.session.commit()
                    # kuvien poisto
                    for kuva in tarina.kuva:
                        poista_kuva = request.form.get(
                            "poista_kuva" + str(kuva.idkuva))
                        if poista_kuva:
                            kuva_name = kuva.kuva
                            path = os.path.join(os.path.abspath(os.path.dirname(
                                __file__)), current_app.config['UPLOAD_FOLDER'], kuva_name)
                            try:
                                os.remove(path)
                            except:
                                pass
                            db.session.delete(kuva)
                            db.session.commit()
                kuva = request.files.get('uusikuva')
                # kuvan tallennus
                if kuva:
                    # tiedostonimeksi jokakerta uniikki nimi turvallisesti
                    tiedostonimi = str(uuid.uuid1()) + "_" + \
                        secure_filename(kuva.filename)
                    path = os.path.join(os.path.abspath(os.path.dirname(
                        __file__)), current_app.config['UPLOAD_FOLDER'], tiedostonimi)
                    kuva.save(path)
                    if nappi == "tallenna_tarina":                        
                        uusikuva = Kuva(kuva=tiedostonimi, idtarina=db.session.query(Tarina).order_by(Tarina.idtarina.desc()).first().idtarina)
                    else:
                        uusikuva = Kuva(kuva=tiedostonimi, idtarina=tarina_id)
                    db.session.add(uusikuva)
                    db.session.commit()
        #tarinoiden poisto
        for tarina in db.session.query(Tarina).filter_by(idmatka=session["viimematka"]):
            if nappi == "poista_tarina " + str(tarina.idtarina):
                for kuva in tarina.kuva:
                    kuva_name = kuva.kuva
                    path = os.path.join(os.path.abspath(os.path.dirname(
                        __file__)), current_app.config['UPLOAD_FOLDER'], kuva_name)
                    try:
                        os.remove(path)
                    except:
                        continue
                db.session.delete(tarina)
                db.session.commit()

            if nappi == "paivita_tarina " + str(tarina.idtarina):
                paivita_tarina = tarina.idtarina

    tarinat = db.session.query(Tarina).filter_by(idmatka=session["viimematka"])
    matka = db.session.query(Matka).get(session["viimematka"])

    return render_template('omatmatkat.html', paivita_tarina=paivita_tarina, tarinat=tarinat, matkat=matkat, matka=matka, lisaa_matka=lisaa_matka, paivita_matka=paivita_matka, user=user, kohteet=kohteet, lisaa_tarina=lisaa_tarina)

@views.route('/matkakohde', methods=['GET', 'POST'])
def kohteet():
    lisaa = False
    paivita = False
    # viimekohde muistaa mikä kohde on ollut valittuna
    if "viimekohde" not in session:
        session["viimekohde"] = db.session.query(
            Matkakohde).first().idmatkakohde

    if request.method == "POST":
        # mitä kohdetta klikattiin
        kohdeid = request.form.get("kohde")
        if kohdeid:
            session["viimekohde"] = kohdeid

        # napien painallukset
        nappi = request.form.get("nappi")
        if nappi == "lisaa":
            lisaa = True

        elif nappi == "paivita":
            paivita = True

        elif nappi == "tallenna":
            # otetaan tiedot formista
            matkakohde = request.form.get("matkakohde")
            maa = request.form.get("maa")
            paikkakunta = request.form.get("paikkakunta")
            kuvateksti = request.form.get("kuvateksti")
            uusikuva = request.files.get("uusikuva")
            # tiedostonimeksi jokakerta uniikki nimi turvallisesti
            tiedostonimi = str(uuid.uuid1()) + "_" + \
                secure_filename(uusikuva.filename)
            path = os.path.join(os.path.abspath(os.path.dirname(
                __file__)), current_app.config['UPLOAD_FOLDER'], tiedostonimi)
            uusikuva.save(path)
            uusikohde = db.session.query(Matkakohde).filter_by(
                kohdenimi=matkakohde).first()

            # jos kohde on jo olemassa
            if uusikohde:
                uusikohde.kohdenimi = matkakohde
                uusikohde.maa = maa
                uusikohde.paikkakunta = paikkakunta
                uusikohde.kuvateksti = kuvateksti
                uusikohde.kuva = tiedostonimi

            # jos kohde ei ollut jo olemassa
            else:
                uusikohde = Matkakohde(
                    kohdenimi=matkakohde, maa=maa, paikkakunta=paikkakunta, kuvateksti=kuvateksti, kuva=tiedostonimi)
                db.session.add(uusikohde)

            db.session.commit()  # tallenetaan muutokset tietokantaan
            # valitaan uusi kohta että se näkyy tallentamisen jälkeen
            session["viimekohde"] = uusikohde.idmatkakohde

        # poistetaan kohde ja sen kuva    (tähän pitäisi lisätä ehto ettei kohteeseen saa littyä tarinoita)
        elif nappi == "poista":
            poistettava_kohde = db.session.query(Matkakohde).filter_by(
                idmatkakohde=session["viimekohde"]).first()
            if poistettava_kohde.tarina:
                flash(
                    'Kohdetta ei voi poistaa koska siihen on liitetty tarina!', category='error')
            else:
                kuva = db.session.query(Matkakohde).get(
                    session["viimekohde"]).kuva
                path = os.path.join(os.path.abspath(os.path.dirname(
                    __file__)), current_app.config['UPLOAD_FOLDER'], kuva)
                try:
                    os.remove(path)
                finally:
                    db.session.query(Matkakohde).filter_by(
                        idmatkakohde=session["viimekohde"]).delete()
                    db.session.commit()
                    session["viimekohde"] = db.session.query(
                        Matkakohde).first().idmatkakohde  # valitaan listan eka kohde

    kohteet = db.session.query(Matkakohde)  # matkakohteet listaa varten
    kohde = db.session.query(Matkakohde).get(
        session["viimekohde"])  # näytettävänä oleva kohde
    # näytetään sivu
    return render_template("kohteet.html", kohteet=kohteet, kohde=kohde, lisaa=lisaa, paivita=paivita, user=current_user)

@views.route('/omattiedot', methods=['GET', 'POST'])
@login_required
def omattiedot():
    muokkaa = False
    user = current_user
    if request.method == 'POST':
        nappi = request.form.get("nappi")
        #jos muokkaa painettu niin muokataan tiedot
        if nappi == "muokkaa":
            muokkaa = True
        else:
            #luetaan syötetyt tiedot
            email = request.form.get('email')
            etunimi = request.form.get('etunimi')
            sukunimi = request.form.get('sukunimi')
            nimimerkki = request.form.get('nimimerkki')
            paikkakunta = request.form.get('paikkakunta')
            esittely = request.form.get('esittely')
            salasana1 = request.form.get('salasana1')
            salasana2 = request.form.get('salasana2')
            uusikuva = request.files.get('uusikuva')
            # tiedostonimeksi jokakerta uniikki nimi turvallisesti
            tiedostonimi = str(uuid.uuid1()) + "_" + \
                secure_filename(uusikuva.filename)
            path = os.path.join(os.path.abspath(os.path.dirname(
                __file__)), current_app.config['UPLOAD_FOLDER'], tiedostonimi)

            #salasanan tulee täsmätä
            if salasana1 != salasana2:
                flash('Salasanat eivät täsmää.', category='error')
            # tallennetaan tietokantaan
            else:
                user.email = email
                user.etunimi = etunimi
                user.sukunimi = sukunimi
                user.nimimerkki = nimimerkki
                user.paikkakunta = paikkakunta
                user.esittely = esittely
                if salasana1 != '':
                    user.password = generate_password_hash(
                        salasana1, method='sha256')
                if user.kuva != 'default_user.png' and uusikuva.filename != '':
                    path2 = os.path.join(os.path.abspath(os.path.dirname(
                        __file__)), current_app.config['UPLOAD_FOLDER'], user.kuva)
                    try:
                        os.remove(path2)
                    except Exception:
                        pass
                if uusikuva.filename:
                    uusikuva.save(path)
                    user.kuva = tiedostonimi
                db.session.commit()
                flash('Tiedot päivitetty', category='success')

    return render_template("omattiedot.html", muokkaa=muokkaa, matkaaja=user, user=user)

@views.route('/jsenet', methods=['GET', 'POST'])
@login_required
def jsenet():
    matkaajat = db.session.query(Matkaaja)
    return render_template("jsenet.html", matkaaja=matkaajat, user=current_user)

@views.route('/porukanmatkat', methods=['GET', 'POST'])
@login_required
def porukanmatkat():
    user = current_user
    matkat = db.session.query(Matka).filter_by(yksityinen=0)
    #jos ei valittu matkaa eka valittuna
    if "viimematka_porukan" not in session:
        session["viimematka_porukan"] = matkat.first().idmatka

    #mikä matka valitaan
    if request.method == "POST":
        idmatka = request.form.get("matka")
        if idmatka:
            session["viimematka_porukan"] = idmatka
    tarinat = db.session.query(Tarina).filter_by(
        idmatka=session["viimematka_porukan"])
    matka = db.session.query(Matka).get(session["viimematka_porukan"])
    return render_template('porukanmatkat.html', tarinat=tarinat, matkat=matkat, matka=matka, user=user)
