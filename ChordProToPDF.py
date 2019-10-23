#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort, redirect, send_file
import os
from sqlalchemy.orm import sessionmaker
from tabledef import *
from create_song import *
from passlib.hash import sha256_crypt
from pandas import read_csv, Index
import shutil
from datetime import datetime
from PyPDF2 import PdfFileMerger
import StringIO
engine = create_engine('sqlite:///users.db', echo=True)

app = Flask(__name__)

port = int(os.getenv('PORT', 80))

f = open('Akkorde.csv', 'rU')
fline = f.readline().replace('\n','')

@app.route('/',methods = ['GET', 'POST'])
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        optionKeys = fline.split(';')
        options = ''
        for o in optionKeys:
            options += '<label ><input type="checkbox" name="keys" value="'+o+'" style="display:none">'+o+'</label>\n'
        if request.method == 'POST':
            fileList = request.files.getlist('files[]')
            keyOptions = request.form.getlist('keys')
            result_type = request.form['result_type']
            folder = 'ChordPro_download_'+datetime.now().strftime('%Y%m%d_%H%M')+'_'+str(len(fileList)*len(keyOptions))+'_'
            path = ('user'+os.sep+session['user']+os.sep+'download'+os.sep+folder+os.sep).encode('ascii','ignore')

            if os.path.exists('user'+os.sep+session['user']+os.sep):
                shutil.rmtree('user'+os.sep+session['user']+os.sep)
            if not os.path.exists(path):
                os.makedirs(path)

            for f in fileList:
                if f.content_type == "text/rtf":
                    for keyOption in keyOptions:
                        print f.filename, keyOption
                        keyOption = keyOption.encode('ascii','ignore')
                        if keyOption == 'original':
                            keyOption = None
                        try:
                            print f
                            convert(path,f,keyOption)
                        except KeyError as e:
                            print str(e) + ' not found in chords for key of the file. Are you sure your file has the correct key?'
                            flash('hi')
                        except Exception as e:
                            print 'error:', e
                    print result_type
                    if result_type == 'PDF':
                        songs = os.listdir(path)
                        print songs
                        merger = PdfFileMerger()
                        result = StringIO.StringIO()
                        for song in songs:
                            merger.append(open(path+song, 'rb'))
                        merger.write(result)
                        result.seek(0)
                        result_name = folder+'.pdf'
                        #return send_file(result,attachment_filename=folder+'.pdf', as_attachment=True)
                    if result_type == 'ZIP':
                        shutil.make_archive('user'+os.sep+session['user']+os.sep+folder, 'zip', 'user'+os.sep+session['user']+os.sep+'download'+os.sep)
                        result = 'user'+os.sep+session['user']+os.sep+folder+'.zip'
                        result_name = folder+'.zip'
                        #return send_file('user'+os.sep+session['user']+os.sep+folder+'.zip',folder+'.zip', as_attachment=True)
                else:
                    return render_template('uploader.html', error = "Please only upload *.rtf files", options = options)
            return send_file(result,attachment_filename=result_name, as_attachment=True)
        else:
            return render_template('uploader.html', options = options)

@app.route('/login', methods=['POST'])
def do_admin_login():
    POST_USERNAME = str(request.form['username']).lower()
    POST_PASSWORD = str(request.form['password'])
    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(User).filter(User.username.in_([POST_USERNAME]))
    result = query.first()
    if result:
        if sha256_crypt.verify( POST_PASSWORD, result.password ):
            session['user'] = result.username
            session['logged_in'] = True
        else:
            return render_template('login.html', error = "Wrong password")
    else:
        return render_template('login.html', error = "User does not exist")
    return redirect('/')#home()

@app.route('/akkorde')
def akkorde():
    if session.get('user') == 'sven' and session.get('logged_in'):
        return render_template('akkorde_uploader.html')
    else:
        return "Hey du bist nicht Sven und hast hier nix zu suchen!"

@app.route('/akkorde_upload', methods = ['GET', 'POST'])
def akkorde_upload():
   if request.method == 'POST':
      f = request.files['file']
      f.save('Akkorde.csv')
      return "Neues 'Akkorde.csv' erfolgreich hochgeladen."

@app.route('/download_akkorde')
def download_akkorde():
    if session.get('user') == 'sven' and session.get('logged_in'):
        return send_file('Akkorde.csv',attachment_filename='Akkorde.csv', as_attachment=True)
    else:
        return "Hey du bist nicht Sven und hast hier nix zu suchen!"

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(host ="0.0.0.0", port = port, debug=False) #host ="0.0.0.0",
