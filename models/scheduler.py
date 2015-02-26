
def task_send (to, subject, message):
    mail.send (to = to, subject = subject, message = message)

from gluon.scheduler import Scheduler
scheduler = Scheduler(db)