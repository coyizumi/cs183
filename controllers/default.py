# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - api is an example of Hypermedia API support and access control
#########################################################################

def index():
    if len(request.args): page=int(request.args[0])
    else: page=0
    items_per_page=3
    limitby=(page*items_per_page,(page+1)*items_per_page+1)
    rows=db().select(db.posting.ALL,limitby=limitby)
    return dict(rows=rows,page=page,items_per_page=items_per_page)

def profile():
    edit = request.vars.edit == 'true'
    content = "string cheese"
    user = None
    if auth.user is not None:
        user = auth.user
    if edit:
        content = SQLFORM.factory(Field('firstname', label='First Name', default=user.first_name if user else ""),
                                  Field('lastname', label='Last Name', default=user.last_name if user else ""),
                                  Field('city', label='City', default=user.city if user else ""),
                                  Field('state', requires=IS_IN_SET(STATES, zero=None), default="California"),
                                  Field('Event Date', 'date', requires=IS_DATE(format=T('%Y-%m-%d'))),
                                  )
        
        #content = SQLFORM.factory(db.userprofile)
    else:
        content = "Not currently editing"
        
    return dict(content=content)

def view_profile():
    user_id = request.args(0) or None
    user = db.auth_user[user_id]
    return dict (user=user)

def view_post():
    post_id = request.args(0) or None
    post = db.posting[post_id]
    user_id = post.user_id
    comments = db(db.comments.post == post).select (orderby=~db.revision.date_posted)
    return dict (post=post, user=user_id, comments=comments)

def add():
    if not auth.user:
        # TODO add some flash here saying "Can only post when logged in"
        # Might be better to require login. Will look that up later
        return dict(content="")
    content = SQLFORM.factory (
        Field('us_state', label="State", default=auth.user.us_state, requires=IS_IN_SET(STATES)),
        Field('city', label="City", default=auth.user.city, requires=IS_NOT_EMPTY()),
        Field('event_date', 'date', label="Event Date", requires=IS_DATE(format=T('%Y-%m-%d'))),
        Field('event_type', label="Event Type", requires=IS_IN_SET(CATEGORY)),
        Field('body', 'text', label='Event Info', requires=IS_NOT_EMPTY()),
        )
    if content.process().accepted:
        db.posting.insert (
            user_id=auth.user,
            us_state=content.vars.us_state,
            city=content.vars.city,
            event_date=content.vars.event_date,
            category=content.vars.event_type,
            body=content.vars.body,
            )
        redirect(URL('default', 'index',))
    return dict(content=content)


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

    rows=db(query).select(limitby=limitby)
    return dict(rows=rows,page=page,items_per_page=items_per_page, list_vars=request.vars)

# http://www.web2pyslices.com/slice/show/1552/search-form

def search():
    form = SQLFORM.factory(
        Field ('us_state', required=True, requires=IS_IN_SET(STATES, zero=None), default='California'),
        Field ('city'),
        Field ('event_date', 'date'),
        Field ('category', requires=IS_EMPTY_OR(IS_IN_SET(CATEGORY))),
        formstyle='divs',
        submit_button='Search',
        )
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
