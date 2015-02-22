# -*- coding: utf-8 -*-
from datetime import datetime

CATEGORY = ['Movies', 'Sports x', 'Disco']
STATES = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois',
'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland',
'Massachussetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri',
'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 
'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 
'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee',
'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 
'Wisconsin', 'Wyoming']

# This is the main table, containing the posts.
db.define_table('posting',
                Field('name'), # Name of the user who posted
                Field('user_id', db.auth_user), # User id of poster, do we need this?
                Field('city'), # City of event
                Field('us_state'), # State of event
                Field('email'), # Email address of poster
                Field('category'), # Category of event
                Field('date_posted', 'datetime'), # Date the event was posted
                Field('event_date', 'date'),
                Field('title'), # Title of posting, do we need this?
                Field('body', 'text'), # Body of posting
                )

db.posting.id.readable = False
db.posting.body.label = 'Body'
db.posting.name.readable = False
# We may want to move this to default.py so we can initialize the time when the post is made
# rather than when the form is created
db.posting.date_posted.default = datetime.utcnow()
db.posting.date_posted.writable = False
db.posting.user_id.default = auth.user_id
db.posting.user_id.writable = db.posting.user_id.readable = False
db.posting.email.requires = IS_EMAIL()
db.posting.email.readable = False
db.posting.category.requires = IS_IN_SET(CATEGORY)
db.posting.category.required = True
db.posting.us_state.requires = IS_IN_SET(STATES,
								   zero=None)
db.posting.us_state.required = True
db.posting.us_state.default='California'
db.posting.city.required = True
db.posting.title.required = True
db.posting.body.required = True
