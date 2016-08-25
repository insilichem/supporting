#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import unicode_literals, print_function, division
import os
import json
from uuid import uuid4
import logging
import datetime
import shutil

from flask import Flask, request, redirect, url_for, render_template

import supporting

logging.basicConfig()
app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    """Handle the upload of a file."""
    form = request.form

    # Create a unique "session ID" for this particular batch of uploads.
    upload_key = str(uuid4())

    # Is the upload using Ajax, or a direct POST by the form?
    is_ajax = False
    if form.get("__ajax", None) == "true":
        is_ajax = True

    # Target folder for these uploads.
    target = "supporting/static/uploads/{}".format(upload_key)
    try:
        os.mkdir(target)
    except:
        if is_ajax:
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
        return redirect(url_for("upload_complete", uuid=upload_key))


@app.route("/reports/<uuid>")
def upload_complete(uuid):
    """The location we send them to at the end of the upload."""

    # Get their reports.
    root = "supporting/static/uploads/{}".format(uuid)
    if not os.path.isdir(root):
        return "Error: UUID not found!"

    paths = [os.path.join(root, fn)
             for fn in os.listdir(root) if os.path.splitext(fn)[1] in ('.qfi', '.out')]
    molecules = supporting.main(paths=paths, output_filename=root + '/supporting.md')

    return render_template("reports.html", uuid=uuid, molecules=molecules)


def ajax_response(status, msg):
    status_code = "ok" if status else "error"
    return json.dumps(dict(
        status=status_code,
        msg=msg,
    ))


def clean_uploads():
    uploads = "supporting/static/uploads/"
    for uuid in os.listdir(uploads):
        path = os.path.join(uploads, uuid)
        delta = datetime.datetime.now() - modification_date(path)
        if delta > datetime.timedelta(days=1):
            shutil.rmtree(path)


def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)