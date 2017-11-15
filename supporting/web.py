#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################
#       Supporting Information Generator       #
# -------------------------------------------- #
# By Jaime RGP <jaime@insilichem.com> @ 2016   #
################################################

from __future__ import unicode_literals, print_function, division, absolute_import
import os
import json
from uuid import uuid4
import datetime
import shutil
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from flask_sslify import SSLify
from .core import main as supporting_main

# logging.basicConfig()
app = Flask(__name__)
if os.environ.get('IN_PRODUCTION'):  # only trigger SSLify if the app is running on Heroku
    sslify = SSLify(app)

UPLOADS = "/tmp"

@app.route("/")
def index():
    return render_template("index.html", uuid= str(uuid4()))


@app.route("/upload", methods=["POST"])
def upload():
    """Handle the upload of a file."""
    form = request.form
    upload_key = form['upload_key']
    # Is the upload using Ajax, or a direct POST by the form?
    is_ajax = False
    if form.get("__ajax", None) == "true":
        is_ajax = True

    # Target folder for these uploads.
    target = os.path.join(UPLOADS, upload_key)
    try:
        os.mkdir(target)
    except:
        if os.path.isdir(target):
            pass
        elif is_ajax:
            return ajax_response(False, "Couldn't create upload directory: {}".format(target))
        else:
            return "Couldn't create upload directory: {}".format(target)

    for upload in request.files.getlist("file"):
        filename = upload.filename.rsplit("/")[0]
        destination = "/".join([target, filename])
        upload.save(destination)

    if is_ajax:
        return ajax_response(True, upload_key)
    else:
        return redirect(url_for("upload_complete", uuid=upload_key,
                                _external=True, _scheme='https'))


@app.route("/reports/<uuid>")
def upload_complete(uuid):
    """The location we send them to at the end of the upload."""

    # Get their reports.
    root = os.path.join(UPLOADS, uuid)
    if not os.path.isdir(root):
        return "Error: UUID not found!"

    paths = [os.path.join(root, fn)
             for fn in os.listdir(root) if os.path.splitext(fn)[1] in ('.qfi', '.out')]
    molecules = supporting_main(paths=paths, output_filename=root + '/supporting.md',
                                image=False)

    for molecule in molecules:
        pdbpath = os.path.join(root, molecule.basename + '.pdb')
        with open(pdbpath, 'w') as f:
            f.write(molecule.pdb_block)

    return render_template("reports.html", uuid=uuid, molecules=molecules)


@app.route('/images/<path:filename>')
def get_image(filename):
    return send_from_directory(UPLOADS, filename, as_attachment=True)


def ajax_response(status, msg):
    status_code = "ok" if status else "error"
    return json.dumps(dict(
        status=status_code,
        msg=msg,
    ))


def clean_uploads():
    for uuid in os.listdir(UPLOADS):
        path = os.path.join(UPLOADS, uuid)
        delta = datetime.datetime.now() - modification_date(path)
        if delta > datetime.timedelta(days=1):
            shutil.rmtree(path)


def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)