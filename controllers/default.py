# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - api is an example of Hypermedia API support and access control
#########################################################################

from datetime import datetime
from datetime import date

def index():
    if auth.user:
        redirect(URL('default', 'list_items', vars=dict(us_state=auth.user.us_state, city=auth.user.city)))
    else:
        redirect(URL('default', 'list_items', vars=dict(us_state='California')))

def view_profile():
    user_id = request.args(0) or None
    user = db.auth_user[user_id]
    if user:
        reviews = db(db.reviews.reviewee_id == user).select()
        # Tally up the totals of each rating
        ratings = dict ()
        for r in RATINGS:
            ratings[r]=0
        for r in reviews:
            ratings[r.rating] += 1
        return dict (user=user, reviews=reviews, ratings=ratings)
    return dict (user=user)

def view_post():
    post_id = request.args(0) or None
    post = db.posting[post_id]
    if post:
        user_id = post.user_id
        comments = db(db.comments.post == post).select (orderby=~db.comments.date_posted)
        invites = db(db.invites.post == post).select()
        return dict (post=post, user=user_id, comments=comments, invites=invites)
    session.flash = T("Invalid post")
    return dict (post=post)

@auth.requires_login()
def delete_post():
    post_id = request.args(0) or None
    post = db.posting[post_id]
    if post and (post.user_id.id == auth.user_id):
        db(db.posting.id == post_id).delete()
    redirect(URL('default', 'index'))

def prune():
    db (db.posting.event_date < date.today()).delete()
    redirect(URL('default', 'index'))

@auth.requires_login()
def add():
    # Create form
    content = SQLFORM.factory (
        Field('title', label="Title", requires=IS_LENGTH(30)),
        Field('us_state', label="State", default=auth.user.us_state, requires=IS_IN_SET(STATES, zero=None)),
        Field('city', label="City", default=auth.user.city, requires=IS_NOT_EMPTY()),
        Field('event_date', 'date', label="Event Date", requires=IS_DATE(format=T('%Y-%m-%d'))),
        Field('event_type', label="Event Type", requires=IS_IN_SET(CATEGORY, zero=None)),
        Field('body', 'text', label='Event Info', requires=[IS_NOT_EMPTY(), IS_LENGTH(300)]),
        )
    # Create new posting from contents of form
    if content.process().accepted:
        post = db.posting.insert (
            user_id=auth.user,
            title=content.vars.title,
            us_state=content.vars.us_state,
            city=content.vars.city,
            event_date=content.vars.event_date,
            category=content.vars.event_type,
            body=content.vars.body,
            )
        # Auto invite the poster
        db.invites.update_or_insert (
            user_id=auth.user,
            post=post,
            )
        redirect(URL('default', 'index',))
    # Return form
    return dict(content=content)

@auth.requires_login()
def add_comment():
    post_id = request.args(0) or None
    post = db.posting[post_id]
    # If post exists
    if post:
        # Create a form
        form = SQLFORM.factory (
            Field ('body', 'text'),
            )
        # Process form and insert new comment
        if form.process().accepted:
            # No need to replace any comments, users can comment multiple times
            db.comments.insert (
                user_id=auth.user,
                post=post,
                date_posted=datetime.utcnow(),
                body=form.vars.body,
                )
            redirect (URL('default', 'view_post', args=[post_id]))
        # Return form
        return dict (content=form, post=post)
    # If post doesn't exist, say so
    session.flash = T("Invalid post")
    return dict (content="Invalid post")

@auth.requires_login()
def add_review():
    user_id = request.args(0) or None
    user = db.auth_user[user_id]
    # If user exists, allow a review to be made
    if user:
        # Review needs only rating and body
        form = SQLFORM.factory (
            Field('rating', requires=IS_IN_SET(RATINGS, zero=None)),
            Field('body', 'text'),
            )
        if form.process().accepted:
            db.reviews.update_or_insert (
                # This dict means that if a review with reviewer_id==auth.user and
                # reviewee_id == user already exists, update it rather than inserting
                # a new one
                dict (reviewer_id=auth.user, reviewee_id=user),
                reviewer_id=auth.user,
                reviewee_id=user,
                rating=form.vars.rating,
                body=form.vars.body,
                )
            redirect (URL('default', 'view_profile', args=[user_id]))
        # Return the form factory
        return dict(content=form, user=user)
    # If user does not exist, say so
    session.flash = T("Invalid user")
    return dict (content="Invalid user")

@auth.requires_login()
def invite():
    post_id = request.args(0) or None
    post = db.posting[post_id]
    if post:
        db.invites.update_or_insert (
            user_id=auth.user,
            post=post,
            )
    redirect (URL('default', 'view_post', args=[post_id]))

def mail_test():
    content = SQLFORM.factory (
        Field('recip', default='coyizumi@gmail.com', requires=IS_EMAIL()),
        Field('subject', default='I like my shoes'),
        Field('message', 'text', default='Oh my'),
        )
    if content.process().accepted:
        
        scheduler.queue_task('task_send',pvars=dict(to=[content.vars.recip],
                                                    subject=content.vars.subject,
                                                    message=content.vars.message),
                                                    timeout=1000)
        session.flash = T('Processed')
    return dict (content=content)

#Used for pagination
# http://web2py.com/books/default/chapter/29/14/other-recipes#Pagination
def list_items():
    if len(request.args): page=int(request.args[0])
    else: page=0
    items_per_page=15
    # Used for pagination
    limitby=(page*items_per_page,(page+1)*items_per_page+1)

    # Apply search terms to query
    state = request.vars.us_state or 'California'
    query = db.posting.us_state == state
    if request.vars.city:
        query &= db.posting.city == request.vars.city
    if request.vars.date:
        query &= db.posting.event_date == request.vars.date
    if request.vars.category:
        query &= db.posting.category == request.vars.category

    # limitby limits the posts returned to a specified range
    rows=db(query).select(limitby=limitby, orderby=db.posting.event_date)
    return dict(rows=rows,page=page,items_per_page=items_per_page, list_vars=request.vars)

# http://www.web2pyslices.com/slice/show/1552/search-form

def search():
    # Create search form
    def_state = 'California'
    if auth.user: def_state = auth.user.us_state
    form = SQLFORM.factory(
        Field ('us_state', required=True, requires=IS_IN_SET(STATES, zero=None), default=def_state),
        Field ('city'),
        Field ('event_date', 'date'),
        Field ('category', requires=IS_EMPTY_OR(IS_IN_SET(CATEGORY))),
        formstyle='divs',
        submit_button='Search',
        )
    # When form is accepted, pass arguments to list_items
    if form.process().accepted:
        list_vars = dict(us_state=form.vars.us_state)
        if form.vars.city:
            list_vars['city'] = form.vars.city
        if form.vars.event_date:
            list_vars['date'] = form.vars.event_date
        if form.vars.category:
            list_vars['category'] = form.vars.category
        redirect (URL ('default', 'list_items', vars=list_vars))

    return dict(form=form)


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_login() 
def api():
    """
    this is example of API with access control
    WEB2PY provides Hypermedia API (Collection+JSON) Experimental
    """
    from gluon.contrib.hypermedia import Collection
    rules = {
        '<tablename>': {'GET':{},'POST':{},'PUT':{},'DELETE':{}},
        }
    return Collection(db).process(request,response,rules)
