#!/usr/bin/env python3
"""Example bot that returns a synchronous response."""

from __future__ import print_function
import httplib2
import os

import flask
from flask import Flask, request, json
import requests

import datetime

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

CLIENT_SECRETS_FILE = 'client_secret.json'

SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'

app = Flask(__name__)
app.secret_key = 'secret'

@app.route('/', methods=['POST'])
def on_event():
    event = request.get_json()
    if event['type'] == 'ADDED_TO_SPACE' and event['space']['type'] == 'ROOM':
        text = 'Thanks for adding me to "%s"!' % event['space']['displayName']
    elif event['type'] == 'MESSAGE':
        text = 'You said: `%s`' % event['message']['text']
    else:
        return
    return json.jsonify({'text': text})
    '''

    """Handles an event from Hangouts Chat."""
    event = request.get_json()
    if event['type'] == 'ADDED_TO_SPACE' and event['space']['type'] == 'ROOM':
        text = 'Thanks for adding me to "%s"!' % event['space']['displayName']
    elif event['type'] == 'MESSAGE':
        request = event['message']['text']

        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        eventsResult = SERVICE.events().list(
                calendarId='primary', timeMin=now, maxResults=3, singleEvents=True,
                orderBy='startTime').execute()
        events = eventsResult.get('items', [])

        if not events:
            text = 'No upcoming events found. Enjoy your free time!'
        else:
            text = ''
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                text = text + start + '\n' + event['summary'] + '\n\n'

    return json.jsonify({'text': text})
    '''
"""
@app.route('/')
def hello_world():
    service = build('calendar', 'v3', credentials=credentials)
    return 'hi'
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 3 events')
    eventsResult = service.events().list(
            calendarId='primary', timeMin=now, maxResults=3, singleEvents=True,
            orderBy='startTime').execute()

    events = eventsResult.get('items', [])

    print(events)

    if not events:
        print('No upcoming events found.')
        text = 'No upcoming events found. Enjoy your free time!'
    else:
        text = ''
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            text = text + start + ' ' + event['summary'] + '\n'
            print(start, event['summary'])
    return text
"""

"""
OAuth Routes
"""

@app.route('/')
def index():
  return print_index_table()


@app.route('/test')
def test_api_request():
  if 'credentials' not in flask.session:
    return flask.redirect('authorize')

  # Load credentials from the session.
  credentials = google.oauth2.credentials.Credentials(
      **flask.session['credentials'])

  drive = googleapiclient.discovery.build(
      API_SERVICE_NAME, API_VERSION, credentials=credentials)

  files = drive.files().list().execute()

  # Save credentials back to session in case access token was refreshed.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  flask.session['credentials'] = credentials_to_dict(credentials)

  return flask.jsonify(**files)


@app.route('/authorize')
def authorize():
  # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES)

  flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

  authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline',
      # Enable incremental authorization. Recommended as a best practice.
      include_granted_scopes='true')

  # Store the state so the callback can verify the auth server response.
  flask.session['state'] = state

  return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
  # Specify the state when creating the flow in the callback so that it can
  # verified in the authorization server response.
  state = flask.session['state']

  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
  flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

  # Use the authorization server's response to fetch the OAuth 2.0 tokens.
  authorization_response = flask.request.url
  flow.fetch_token(authorization_response=authorization_response)

  # Store credentials in the session.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  credentials = flow.credentials
  flask.session['credentials'] = credentials_to_dict(credentials)

  return flask.redirect(flask.url_for('test_api_request'))


@app.route('/revoke')
def revoke():
  if 'credentials' not in flask.session:
    return ('You need to <a href="/authorize">authorize</a> before ' +
            'testing the code to revoke credentials.')

  credentials = google.oauth2.credentials.Credentials(
    **flask.session['credentials'])

  revoke = requests.post('https://accounts.google.com/o/oauth2/revoke',
      params={'token': credentials.token},
      headers = {'content-type': 'application/x-www-form-urlencoded'})

  status_code = getattr(revoke, 'status_code')
  if status_code == 200:
    return('Credentials successfully revoked.' + print_index_table())
  else:
    return('An error occurred.' + print_index_table())


@app.route('/clear')
def clear_credentials():
  if 'credentials' in flask.session:
    del flask.session['credentials']
  return ('Credentials have been cleared.<br><br>' +
          print_index_table())


def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}
  
def print_index_table():
    return ('<table>' +
      '<tr><td><a href="/test">Test an API request</a></td>' +
      '<td>Submit an API request and see a formatted JSON response. ' +
      '    Go through the authorization flow if there are no stored ' +
      '    credentials for the user.</td></tr>' +
      '<tr><td><a href="/authorize">Test the auth flow directly</a></td>' +
      '<td>Go directly to the authorization flow. If there are stored ' +
      '    credentials, you still might not be prompted to reauthorize ' +
      '    the application.</td></tr>' +
      '<tr><td><a href="/revoke">Revoke current credentials</a></td>' +
      '<td>Revoke the access token associated with the current user ' +
      '    session. After revoking credentials, if you go to the test ' +
      '    page, you should see an <code>invalid_grant</code> error.' +
      '</td></tr>' +
      '<tr><td><a href="/clear">Clear Flask session credentials</a></td>' +
      '<td>Clear the access token currently stored in the user session. ' +
      '    After clearing the token, if you <a href="/test">test the ' +
      '    API request</a> again, you should go back to the auth flow.' +
      '</td></tr></table>')

if __name__ == '__main__':
    # remove in prod:
#    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'    
    app.run(port=8080, debug=True)

