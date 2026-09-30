# PROJECT: example/digest-tagger (synthetic fixture)

## FILE: README.md
digest-tagger: a small Flask app for a hobby newsletter. Subscribers sign up with their email; each week the editor pastes in links and the app suggests a topic tag for each one using Jev, then the editor builds the digest.

## FILE: app.py
1: import sqlite3, os
2: from flask import Flask, request, render_template
3: from typesafe_sdk import TypeSafeClient, choice
5: client = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"])
6: TOPICS = ["tools", "research", "tutorials", "news", "other"]
14:     db().execute("INSERT INTO subscribers(email) VALUES (?)", (request.form["email"],))
23:     r = client.system_one(model="jev-1.13.0", state={"link": link},
24:         questions={"topic": choice("Which topic best fits `link`?", options=TOPICS)})
25:     # the editor sees the suggestion in a dropdown and can change it before saving
