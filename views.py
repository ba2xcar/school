from flask import Flask, render_template, request, flash, url_for, redirect
import psycopg2 as psy
import datetime

def ConnexionDB():
    try:
        #Connexion à la base de données
        connection = psy.connect(user="postgres",password="",
                                    host="localhost",
                                    port="5432",
                                    database="scolaire"
                                    )
        return connection
    except (Exception) as error :
        print ("Problème de connexion au serveur PostgreSQL", error)
connection = ConnexionDB()
curseur = connection.cursor()
app = Flask(__name__) #permet de localiser les ressources cad les templates
app.secret_key = 'some_secret'

#**************************************ACCUEIL************************************
@app.route('/')
def index():
    return render_template("index.html")
@app.route('/accueil')
def accueil():
    requete_liste_promo = """select id_promo FROM promotion """
    curseur.execute(requete_liste_promo)
    result_nompro = curseur.fetchall()
#------------------------------------------------------DIAGRAMME EN BAR LISTE APPRENANT PAR PROMOTION---------------------------------
    liste_app=[]
    compt_app=[]
    promo_label=[]
    for val in result_nompro:
        requete_liste_pro = """select count(matricule) ,promotion.libelle FROM apprenant,promotion where 
        promotion.id_promo=apprenant.id_promo and apprenant.id_promo=%s  group by promotion.libelle"""
        curseur.execute(requete_liste_pro,(val[0],))
        result = curseur.fetchall()
        if result==[]:
            sql="select libelle from promotion where id_promo=%s"
            curseur.execute(sql,(val[0],))
            rs=curseur.fetchall()
            for v in rs:
                tu=[(0,v[0])]
            liste_app.append(tu)
        else:
            liste_app.append(result)
    for val in liste_app:
        compt_app.append(val[0][0])
    for val in liste_app:
        promo_label.append(val[0][1])
#-----------------------------------------------------DIAGRAMME CIRCULAIRE-----------------------------------
    requete_liste = "SELECT statut FROM apprenant"
    curseur.execute(requete_liste)
    result = curseur.fetchall()
    annule=0
    suspendre=0
    reinscrit=0
    inscrit=0
    for val in result:
        if val[0]=='annuler':
            annule=annule+1
        elif val[0]=='suspendre':
            suspendre=suspendre+1
        elif val[0]=='reinscrit':
            reinscrit=reinscrit+1
        elif val[0]=='inscrit':
            inscrit=inscrit+1
    liste_statut=[inscrit,reinscrit,suspendre,annule]

    return render_template('graphique.html',compt_app=compt_app,promo_label=promo_label,liste_statut=liste_statut)
#---------------------------------------------------------------------------------
@app.route('/', methods=["POST"])
def login():    
    username=request.form['username']
    password=request.form['password']
    requete_liste_promo = "SELECT username,password FROM authentification"
    curseur.execute(requete_liste_promo)
    result = curseur.fetchall()
    
    for val in result:
        if username==val[0] and password==val[1]:
            return redirect(url_for('accueil'))
        else:
            flash("WARNING : Nom d'utilisateur ou mot de passe invalide")
            return render_template("index.html")

#*********************************************************************************

#***************************************AJOUT APPRENANT*******************************
@app.route('/scolarite/inscription')
def ajouter_apprenant():
    requete_liste_promo = "SELECT id_promo,libelle FROM promotion WHERE date_debut>=DATE( NOW() )"
    curseur.execute(requete_liste_promo)
    result = curseur.fetchall()
    valeurs=result   

    requete_liste_matricule = "SELECT max(id_app) FROM apprenant"
    curseur.execute(requete_liste_matricule)
    result_matricule = curseur.fetchall()
    for mat in result_matricule:
        matricule=mat[0]
    date_actu=datetime.datetime.today().strftime('%Y')

    if matricule == None:
        num=1
        val='-'+str(num)+'-'
        gen_mat = "SA"+val+str(date_actu)
    else:
        num=matricule+1
        val='-'+str(num)+'-'
        gen_mat="SA"+val+str(date_actu)
    return render_template("ajouter_apprenant.html",valeurs=valeurs,gen_mat=gen_mat)

#---------------------------------------------------------------------------------
@app.route('/scolarite/inscription', methods=["POST"])
def insertion_app():
    matricule = request.form["matricule"]
    prenom = request.form["prenom"]
    nom = request.form["nom"]
    sexe = request.form["sexe"]
    date_naissance = request.form["date_naissance"]
    lieu_naissance = request.form["lieu_naissance"]
    adresse = request.form["adresse"]
    email = request.form["email"].lower()
    telephone = request.form["telephone"]
    promotion = request.form["promo"]
    statut = 'inscrit'
    data=(matricule,prenom,nom,sexe,date_naissance,lieu_naissance,adresse,email,telephone,promotion,statut)

    requete_libelle_promo = "SELECT telephone,email FROM apprenant"
    curseur.execute(requete_libelle_promo)
    apprenant = curseur.fetchall()
    control_app=False

    for app in apprenant:
        if app[0] == telephone or app[1].lower()==email.lower():
            control_app = True
            break
    if control_app == True:
        flash("WARNING : L'apprenant existe déjà")
        requete_liste_promo = "SELECT id_promo,libelle FROM promotion WHERE date_debut>DATE( NOW() )"
        curseur.execute(requete_liste_promo)
        result = curseur.fetchall()
        valeurs=result   

        requete_liste_matricule = "SELECT max(id_app) FROM apprenant"
        curseur.execute(requete_liste_matricule)
        result_matricule = curseur.fetchall()
        for mat in result_matricule:
            matric=mat[0]
        date_actu=datetime.datetime.today().strftime('%Y')

        if matric == None:
            num=1
            val='-'+str(num)+'-'
            gen_mat = "SA"+val+str(date_actu)
        else:
            num=matric+1
            val='-'+str(num)+'-'
            gen_mat="SA"+val+str(date_actu)
        return render_template("ajouter_apprenant.html",valeurs=valeurs,gen_mat=gen_mat,prenom=prenom,nom=nom,date_naissance=date_naissance,lieu_naissance=lieu_naissance,adresse=adresse,email=email,telephone=telephone)
    elif control_app == False: 
        requete_ajout_app = """INSERT INTO apprenant 
                            (matricule,prenom,nom,sexe,date_naissance,lieu_naissance,adresse,email,telephone,id_promo,statut) 
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        curseur.execute(requete_ajout_app,data)
        connection.commit() 
        flash("SUCCESS : Apprenant ajouté avec succès!!!")
        return redirect(url_for('ajouter_apprenant'))

#**********************************************************************************

#***************************************LISTE APPRENANT POUR ANNULER OU SUPPRIMER****************************
@app.route('/promo/lister&app')
def lister_apprenant():
    
    requete_liste_app = """SELECT matricule,prenom,nom,sexe,lieu_naissance,adresse,
                        telephone,email,statut,promotion.libelle FROM apprenant,promotion
                        WHERE promotion.id_promo=apprenant.id_promo and promotion.date_debut>=DATE( NOW() ) and 
                        (statut = 'inscrit' OR statut = 'reinscrit')
                        ORDER BY matricule """
    curseur.execute(requete_liste_app)
    result=curseur.fetchall()

    requete_liste_promo = "SELECT id_promo,libelle FROM promotion WHERE date_debut>=DATE( NOW() )"
    curseur.execute(requete_liste_promo)
    requete_promo = curseur.fetchall()
    return render_template("lister_apprenant_action.html",result=result,requete_promo=requete_promo)

@app.route('/promo/lister&app', methods = ['POST'])
def lister_appar_promo():
   
    id_promo = request.form["promo"]
    requete_liste_app = """SELECT matricule,prenom,nom,sexe,lieu_naissance,adresse,
                            telephone,email,statut,promotion.libelle FROM apprenant,promotion 
                            WHERE promotion.id_promo = apprenant.id_promo and apprenant.id_promo=%s 
                            and (statut = 'inscrit' OR statut = 'reinscrit' ) ORDER BY matricule"""
    curseur.execute(requete_liste_app,(id_promo,))
    result=curseur.fetchall()

    requete_liste_promo = "SELECT id_promo,libelle FROM promotion WHERE date_debut>=DATE( NOW() )"
    curseur.execute(requete_liste_promo)
    requete_promo = curseur.fetchall()
    return render_template("lister_apprenant_action.html",result=result,requete_promo=requete_promo)
#------------------------------------------LISTE APPRENANT PAR PROMO-------------------------------------

    

#************************************************************************************************************

#***************************************LISTE APPRENANT POUR MODIFIER****************************************
@app.route('/scolarite/lister&app')
def lister_apprenant_mod():
    requete_liste_app = """SELECT matricule,prenom,nom,sexe,adresse,
                        telephone,email,statut,promotion.libelle FROM apprenant,promotion WHERE
                        promotion.id_promo=apprenant.id_promo ORDER BY matricule """
    curseur.execute(requete_liste_app)
    result=curseur.fetchall() 

    requete_liste_promo = "SELECT id_promo,libelle FROM promotion"
    curseur.execute(requete_liste_promo)
    requete_promo = curseur.fetchall()
    return render_template("lister_apprenant_mod.html",result=result,requete_promo=requete_promo)

@app.route('/scolarite/lister&app', methods = ['POST'])
def lister_apppar_promo():
    id_promo = request.form["promo"]
    requete_liste_app = """SELECT matricule,prenom,nom,sexe,adresse,
                        telephone,email,statut,promotion.libelle FROM apprenant,promotion 
                        WHERE promotion.id_promo=apprenant.id_promo and promotion.id_promo=%s ORDER BY matricule"""
    curseur.execute(requete_liste_app,(id_promo,))
    result=curseur.fetchall()

    requete_liste_promo = "SELECT id_promo,libelle FROM promotion"
    curseur.execute(requete_liste_promo)
    requete_promo = curseur.fetchall()
    return render_template("lister_apprenant_mod.html",result=result,requete_promo=requete_promo)

#****************************************************************************************************

#****************************************AJOUT PROMO********************************
@app.route('/promo/nouveau')
def ajouter_promo():
    requete_liste_ref = "select * from referentiel"
    curseur.execute(requete_liste_ref)
    result=curseur.fetchall()
    return render_template("ajouter_promo.html",result=result)

#-----------------------------------------------------------------------------------
@app.route('/promo/nouveau', methods=["POST"])

def insertion_promo():

    nom_promo = request.form["nom_promo"]
    date_debut = request.form["startdate"]
    date_fin = request.form["enddate"]
    id_ref = request.form["id_ref"]
    
    if date_debut>=date_fin:
        flash("WARNING : La date de début doit être inférieur à la date de fin")
        requete_liste_ref = "select * from referentiel"
        curseur.execute(requete_liste_ref)
        result=curseur.fetchall()
        return render_template("ajouter_promo.html",nom_promo=nom_promo,date_debut=date_debut,date_fin=date_fin,result=result)
    else:
        requete_libelle_promo = "select libelle from promotion"
        curseur.execute(requete_libelle_promo)
        libelle=curseur.fetchall()
        control_promo=False

        for lib in libelle:
            if lib[0].lower() == nom_promo.lower():
                control_promo = True
                break

        if control_promo == True:
            flash("WARNING : La promotion existe déjà")
            requete_liste_ref = "select * from referentiel"
            curseur.execute(requete_liste_ref)
            result=curseur.fetchall()
            return render_template("ajouter_promo.html",nom_promo=nom_promo,date_debut=date_debut,date_fin=date_fin,result=result)

        else: 
            requete_ajout_promo = "INSERT INTO promotion (libelle,date_debut,date_fin,id_ref) VALUES (%s,%s,%s,%s)"
            data = (nom_promo,date_debut,date_fin,id_ref)
            print(data)
            curseur.execute(requete_ajout_promo,data)
            connection.commit()
            flash("SUCCES : Promotion ajoutée avec succès!!!")
            return redirect(url_for('ajouter_promo'))
#***********************************************************************************

#****************************************AJOUT REFERENTIEL***************************
@app.route('/referent/nouveau')
def ajouter_ref():
    return render_template("ajouter_ref.html")

#-----------------------------------------------------------------------------------
@app.route('/referent/nouveau', methods=["POST"])
def insertion_ref():
    nom_ref = request.form["nom_ref"]
    
    requete_liste_ref = """SELECT libelle FROM referentiel"""
    curseur.execute(requete_liste_ref)
    result_nomref = curseur.fetchall()
    control_ref=False

    for val in result_nomref:
        if val[0].lower() == nom_ref.lower():
            control_ref = True
            break
    if control_ref == True:
        flash("WARNING : Le référentiel existe déjà")
        return render_template("ajouter_ref.html",nom_ref=nom_ref)
    else:
        requete_ajout_ref = "INSERT INTO referentiel (libelle) VALUES (%s)"
        curseur.execute(requete_ajout_ref,(nom_ref,))
        connection.commit()
        flash("SUCCESS : Référentiel ajouté avec succès!!!")
        return redirect(url_for('insertion_ref'))
#************************************************************************************************************

#***************************************LISTE REFERENTIEL*****************************************************
@app.route('/referent/modifier')
def lister_referentiel():
    requete_liste_ref = """SELECT * FROM referentiel ORDER BY id_ref"""
    curseur.execute(requete_liste_ref)
    result=curseur.fetchall() 
    return render_template("lister_referentiel.html",result=result)
#******************************************************************************************************

#****************************************MODIFIER REFERENTIEL*******************************************
@app.route('/referent/modifier&<string:id_data>', methods = ['GET','POST'])
def modifier_referentiel(id_data):
    if request.method == 'GET':
        requete_ajout_app = """select libelle FROM referentiel WHERE id_ref=%s"""
        data= (id_data,)
        curseur.execute(requete_ajout_app,data)
        result_up_ref = curseur.fetchall()
        return render_template("modifier_referentiel.html",result_up_ref=result_up_ref)

    elif request.method == 'POST':
        nom_ref = request.form["nom_ref"]
            
        requete_liste_ref = """SELECT libelle FROM referentiel WHERE id_ref!=%s """
        curseur.execute(requete_liste_ref,(id_data,))
        result_nomref = curseur.fetchall()
        control_ref=False

        for val in result_nomref:
            if val[0].lower() == nom_ref.lower():
                control_ref = True
                break
        if control_ref == True:
            flash("WARNING : Le référentiel existe déjà")
            requete_ajout_app = """select libelle FROM referentiel WHERE id_ref=%s"""
            data= (id_data,)
            curseur.execute(requete_ajout_app,data)
            result_up_ref = curseur.fetchall()
            return render_template("modifier_referentiel.html",result_up_ref=result_up_ref)
        else:
            requete_up_ref = """UPDATE referentiel SET libelle=%s WHERE id_ref=%s"""
            data_up_ref = (nom_ref,id_data)
            curseur.execute(requete_up_ref,data_up_ref)
            connection.commit()
            flash("SUCCESS : Référentiel modifié avec succès!!!")
            return redirect(url_for('lister_referentiel'))
#********************************************************************************************************

#****************************************MODIFIER APPRENANT*********************************************
@app.route('/scolarite/modifier&<string:id_data>', methods = ['GET','POST'])
def modifier(id_data):
    if request.method == 'GET':
        requete_ajout_app = """ select matricule,prenom,nom,sexe,date_naissance,lieu_naissance,adresse,email,telephone,
                                apprenant.id_promo,promotion.libelle from apprenant, promotion where
                                apprenant.id_promo = promotion.id_promo and matricule=%s"""
        data= (id_data,)
        curseur.execute(requete_ajout_app,data)
        result_up = curseur.fetchall()

        for val in result_up:
            data_promo=val[9]
            break

        requete_promo = "SELECT * FROM promotion WHERE id_promo!=%s "
        curseur.execute(requete_promo,(data_promo,))
        result_promo = curseur.fetchall()
        return render_template("modifier_apprenant.html",result_up=result_up,result_promo=result_promo)
    elif request.method == 'POST':
        prenom = request.form["prenom"]
        nom = request.form["nom"]
        sexe = request.form["sexe"]
        date_naissance = request.form["date_naissance"]
        lieu_naissance = request.form["lieu_naissance"]
        adresse = request.form["adresse"]
        email = request.form["email"]
        telephone = request.form["telephone"]
        promotion = request.form["promo"]
        
        requete_libelle_promo = "select telephone,email from apprenant WHERE matricule!=%s "
        curseur.execute(requete_libelle_promo,(id_data,))
        apprenant = curseur.fetchall()
        control_app=False

        for app in apprenant:
            if app[0] == telephone and app[1].lower()==email.lower():
                control_app = True
                break
        if control_app == True:
            flash("l'apprenant existe déjà")
            print("l'utilisateur existe déjà")
            return redirect(url_for('index'))     
        else: 

            requete_up_app = """UPDATE apprenant SET prenom=%s, nom=%s, sexe=%s, date_naissance=%s, 
                            lieu_naissance=%s, adresse=%s, email=%s, telephone=%s, id_promo=%s
                            WHERE matricule=%s"""    
            data_up = (prenom,nom,sexe,date_naissance,lieu_naissance,adresse,email,telephone,promotion,id_data)
            curseur.execute(requete_up_app,data_up)
            connection.commit()
            return redirect(url_for('lister_apprenant'))
#************************************************************************************************************#

#****************************************ANNULER APPRENANT***************************************************#
@app.route('/scolarite/lister&annuler&<string:id_data>', methods = ['GET','POST'])
def annuler(id_data):
    statut = "annuler"
    data_up_annuler = (statut,id_data)
    requete_up_annuler = """UPDATE apprenant SET statut=%s WHERE matricule=%s"""    
    curseur.execute(requete_up_annuler, data_up_annuler)
    connection.commit()
    return redirect(url_for('lister_apprenant'))
#************************************************************************************************************#

#****************************************SUSPENDRE APPRENANT*************************************************#
@app.route('/scolarite/lister&suspendre&<string:id_data>', methods = ['GET','POST'])
def suspendre(id_data):
    statut = "suspendre"
    data_up_suspendre = (statut,id_data)
    requete_up_suspendre = """UPDATE apprenant SET statut=%s WHERE matricule=%s"""    
    curseur.execute(requete_up_suspendre, data_up_suspendre)
    connection.commit()
    return redirect(url_for('lister_apprenant'))
#************************************************************************************************************#

#********************************************LISTE ANNULEE*********************************************#
@app.route('/scolarite/annuler')
def lister_annuler():
    requete_liste_app = """select matricule,prenom,nom,sexe,adresse,
                        telephone,email,statut,promotion.libelle FROM apprenant,promotion WHERE 
                        promotion.id_promo=apprenant.id_promo and statut = 'annuler' """
    curseur.execute(requete_liste_app)
    result=curseur.fetchall() 
    requete_promo = "SELECT id_promo,libelle FROM promotion WHERE date_debut>DATE( NOW() )"
    curseur.execute(requete_promo)
    result_promo = curseur.fetchall()
    return render_template("liste_annuler_actuel.html",result=result,result_promo=result_promo)

@app.route('/scolarite/annuler', methods = ['POST'])
def lister_annuler_precedent():
    id_promo = request.form["promo"]
    if id_promo != "passe" and id_promo != "cours":
        requete_liste_app = """select matricule,prenom,nom,sexe,date_naissance,lieu_naissance,adresse,
                            telephone,email,promotion.libelle,statut from apprenant,promotion 
                            WHERE promotion.id_promo=apprenant.id_promo and statut = 'annuler' and promotion.id_promo=%s"""
        curseur.execute(requete_liste_app,(id_promo,))
        result=curseur.fetchall()

        requete_promo = "SELECT id_promo,libelle FROM promotion WHERE date_debut>=DATE( NOW() )"
        curseur.execute(requete_promo)
        result_promo = curseur.fetchall()
        return render_template("liste_annuler_actuel.html",result=result,result_promo=result_promo)

    elif id_promo=="passe":
        requete_liste_app = """select matricule,prenom,nom,sexe,date_naissance,lieu_naissance,adresse,
                            telephone,email,promotion.libelle,statut from apprenant,promotion 
                            WHERE promotion.id_promo=apprenant.id_promo and statut = 'annuler' and promotion.date_debut<DATE( NOW() ) """
        curseur.execute(requete_liste_app,(id_promo,))
        result=curseur.fetchall() 

        requete_promo = "SELECT id_promo,libelle FROM promotion WHERE date_debut<DATE( NOW() )"
        curseur.execute(requete_promo)
        result_promo = curseur.fetchall()
        return render_template("liste_annuler_actuel.html",result=result,result_promo=result_promo,actuel="actu")
    elif id_promo=="cours":
        requete_liste_app = """select matricule,prenom,nom,sexe,date_naissance,lieu_naissance,adresse,
                            telephone,email,promotion.libelle,statut from apprenant,promotion 
                            WHERE promotion.id_promo=apprenant.id_promo and statut = 'annuler' """
        curseur.execute(requete_liste_app,(id_promo,))
        result=curseur.fetchall() 

        requete_promo = "SELECT id_promo,libelle FROM promotion WHERE date_debut>=DATE( NOW() )"
        curseur.execute(requete_promo)
        result_promo = curseur.fetchall()
        return render_template("liste_annuler_actuel.html",result=result,result_promo=result_promo,actuel="passe")

#************************************************************************************************************

#********************************************LISTE SUSPENDRE*********************************************#
@app.route('/scolarite/suspendre')
def lister_suspendre():
    requete_liste_promo = "SELECT id_promo,libelle FROM promotion"
    curseur.execute(requete_liste_promo)
    requete_promo = curseur.fetchall()

    requete_liste_app = """select matricule,prenom,nom,sexe,date_naissance,lieu_naissance,adresse,
                        telephone,email from apprenant WHERE statut = 'suspendre' """
    curseur.execute(requete_liste_app)
    result=curseur.fetchall() 
    return render_template("liste_suspendre.html",result=result,requete_promo=requete_promo)
#--------------------------------------------------------------------------------------------------------
@app.route('/scolarite/suspendre', methods = ['POST'])
def lister_appro_suspendre():
    id_promo = request.form["promo"]
    requete_liste_app = """SELECT matricule,prenom,nom,sexe,date_naissance,lieu_naissance,adresse,
                        telephone,email,promotion.libelle,statut FROM apprenant,promotion 
                        WHERE promotion.id_promo=apprenant.id_promo and statut = 'suspendre' and promotion.id_promo=%s"""
    curseur.execute(requete_liste_app,(id_promo,))
    result=curseur.fetchall()

    requete_liste_promo = "SELECT id_promo,libelle FROM promotion"
    curseur.execute(requete_liste_promo)
    requete_promo = curseur.fetchall()
    return render_template("liste_suspendre.html",result=result,requete_promo=requete_promo)
#************************************************************************************************************

#***********************************************REINSCRIRE APPRENANT******************************************
@app.route('/scolarite/suspendre&<string:id_data>', methods = ['GET','POST'])
def reinscrire(id_data):
    if request.method == 'GET':
        requete_ajout_app = """ SELECT prenom,nom,sexe,date_naissance,lieu_naissance,adresse,email,telephone,
                                apprenant.id_promo,promotion.libelle FROM apprenant, promotion WHERE
                                apprenant.id_promo = promotion.id_promo AND matricule=%s"""
        data= (id_data,)
        curseur.execute(requete_ajout_app,data)
        result_up = curseur.fetchall()

        for val in result_up:
            data_promo=val[8]
            break
        
        requete_promo = "SELECT * FROM promotion WHERE date_debut>=DATE( NOW() ) AND id_promo!=%s"
        curseur.execute(requete_promo,(data_promo,))
        result_promo = curseur.fetchall()

        requete_promo_before = "SELECT * FROM promotion WHERE date_debut>=DATE( NOW() ) AND id_promo=%s"
        curseur.execute(requete_promo_before,(data_promo,))
        result_promo_before = curseur.fetchall()
        return render_template("reinscrire_apprenant.html",result_up=result_up,result_promo=result_promo,result_promo_before=result_promo_before)
    elif request.method == 'POST':
        promotion = request.form["promo"]
        statut = "reinscrit"
        requete_up_app = """UPDATE apprenant SET statut=%s, id_promo=%s
                        WHERE matricule=%s"""    
        data_up = (statut,promotion,id_data)
        curseur.execute(requete_up_app,data_up)
        connection.commit()
        return redirect(url_for('lister_apprenant'))
#*********************************************************************************************************

#***************************************LISTE PROMOTION*****************************************************
@app.route('/promo/modifier')
def lister_promo():
    requete_liste_promo = """SELECT id_promo,promotion.libelle,date_debut,date_fin,referentiel.libelle
                                FROM promotion,referentiel WHERE 
                                referentiel.id_ref = promotion.id_ref ORDER BY promotion.id_promo"""
    curseur.execute(requete_liste_promo)
    result=curseur.fetchall() 
    return render_template("lister_promo.html",result=result)
#************************************************************************************************************

#***********************************************MODIFIER PROMOTION********************************************
@app.route('/promo/modifier&<string:id_data>', methods = ['GET','POST'])
def modifier_promo(id_data):
    if request.method == 'GET':
        requete_modif_promo = """SELECT promotion.libelle,promotion.id_ref,referentiel.libelle,date_debut,
                                date_fin FROM promotion,referentiel WHERE referentiel.id_ref = promotion.id_ref  
                                 and id_promo=%s"""
        data= (id_data,)
        curseur.execute(requete_modif_promo,data)
        result_up_promo = curseur.fetchall()

        for val in result_up_promo:
            data_ref=val[1]
            break

        requete_promo = "SELECT * FROM referentiel WHERE id_ref!=%s "
        curseur.execute(requete_promo,(data_ref,))
        result_ref = curseur.fetchall()
        return render_template("modifier_promo.html",result_up_promo=result_up_promo,result_ref=result_ref)
    elif request.method == 'POST':
        nom_promo = request.form["nom_promo"]
        date_debut = request.form["startdate"]
        date_fin = request.form["enddate"]
        id_ref = request.form["id_ref"]
            
        requete_libelle_promo = "SELECT libelle FROM promotion WHERE id_promo!=%s"
        curseur.execute(requete_libelle_promo,(id_data,))
        libelle=curseur.fetchall()
        control_promo=False

        for lib in libelle:
            if lib[0].lower() == nom_promo.lower():
                control_promo = True
                break

        if control_promo == True:
            flash("WARNING : La promotion existe déjà")
            #Une fonction peut gérer ça
            requete_modif_promo = """SELECT promotion.libelle,promotion.id_ref,referentiel.libelle,date_debut,date_fin
                                FROM promotion,referentiel WHERE 
                                referentiel.id_ref = promotion.id_ref and id_promo=%s"""
            data= (id_data,)
            curseur.execute(requete_modif_promo,data)
            result_up_promo = curseur.fetchall()

            for val in result_up_promo:
                data_ref=val[1]
                break

            requete_promo = "SELECT * FROM referentiel WHERE id_ref!=%s "
            curseur.execute(requete_promo,(data_ref,))
            result_ref = curseur.fetchall()
            return render_template("modifier_promo.promotion,promotion,promotion,promotion,promotion,promotion,promotion,html",result_up_promo=result_up_promo,result_ref=result_ref)

        else: 
            requete_up_promo = """UPDATE promotion SET libelle=%s, date_debut=%s, date_fin=%s, id_ref=%s
                            WHERE id_promo=%s"""    
            data_up_promo = (nom_promo,date_debut,date_fin,id_ref,id_data)
            curseur.execute(requete_up_promo,data_up_promo)
            connection.commit()
            flash("SUCCESS : Promotion modifiée avec succès!!!")
            return redirect(url_for('lister_promo'))
#*************************************************************************************************************#

#**********************************************GRAPHIQUE*****************************************************
#-------------------------------------------------HISTOGRAMME-----------------------------------------------

if __name__ == '__main__': #si le fichier est executer alors execute le bloc
    app.run(debug=True) #debug=True relance le serveur à chaque modification



