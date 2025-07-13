import time
import uuid
from datetime import datetime

from caldav.compatibility_hints import FeatureSet
from caldav.lib.error import NotFoundError, AuthorizationError
from caldav.calendarobjectresource import Event, Todo, Journal

from .checks_base import Check

## WORK IN PROGRESS

## TODO: We need some collector framework that can collect all checks,
## build a dependency graph and mapping from a feature to the relevant
## check.

class CheckGetCurrentUserPrincipal(Check):
    """
    Checks support for get-current-user-principal
    """
    features_to_be_checked = {'get-current-user-principal'}
    depends_on = set()
    def _run_check(self):
        try:
            self.checker.principal = self.client.principal()
            self.feature_checked('get-current-user-principal')
        except:
            self.checker.principal = None
            self.feature_checked('get-current-user-principal', False)
        return self.checker.principal

class CheckMakeDeleteCalendar(Check):
    """
    Checks (relatively) thoroughly that it's possible to create a calendar and delete it
    """
    features_to_be_checked = {'get-current-user-principal.has-calendar', 'create-calendar.auto', 'create-calendar', 'create-calendar.set-displayname', 'delete-calendar', 'delete-calendar.free-namespace' }
    depends_on = { CheckGetCurrentUserPrincipal }

    def _try_make_calendar(self, cal_id, **kwargs):
        """
        Does some attempts on creating and deleting calendars, and sets some
        flags - while others should be set by the caller.
        """
        calmade = False

        ## In case calendar already exists ... wipe it first
        try:
            self.checker.principal.calendar(cal_id=cal_id).delete()
        except:
            pass

        ## create the calendar
        try:
            cal = self.checker.principal.make_calendar(cal_id=cal_id, **kwargs)
            ## calendar creation probably went OK, but we need to be sure...
            cal.events()
            ## calendar creation must have gone OK.
            calmade = True
            self.checker.principal.calendar(cal_id=cal_id).events()
            self.feature_checked("create-calendar")
            if kwargs.get("name"):
                try:
                    name = "A calendar with this name should not exist"
                    self.checker.principal.calendar(name=name).events()
                    breakpoint() ## TODO - do something better here
                except:
                    ## This is not the exception, this is the normal
                    try:
                        cal2 = self.checker.principal.calendar(name=kwargs["name"])
                        cal2.events()
                        assert cal2.id == cal.id
                        self.feature_checked("create-calendar.set-displayname")
                    except:
                        self.feature_checked("create-calendar.set-displayname", False)

        except Exception as e:
            ## calendar creation created an exception.  Maybe the calendar exists?
            ## in any case, return exception
            cal = self.checker.principal.calendar(cal_id=cal_id)
            try:
                cal.events()
            except:
                cal = None
            if not cal:
                ## cal not made and does not exist, exception thrown.
                ## Caller to decide why the calendar was not made
                return (False, e)

        assert cal

        try:
            cal.delete()
            try:
                cal = self.checker.principal.calendar(cal_id=cal_id)
                events = cal.events()
            except NotFoundError:
                cal = None
            ## Delete throw no exceptions, but was the calendar deleted?
            if not cal or (
                self.flags_checked.get(
                    "non_existing_calendar_found" and len(events) == 0
                )
            ):
                self.feature_checked("delete-calendar")
                ## Calendar probably deleted OK.
                ## (in the case of non_existing_calendar_found, we should add
                ## some events to the calendar, delete the calendar and make
                ## sure no events are found on a new calendar with same ID)
            else:
                ## Calendar not deleted.
                ## Perhaps the server needs some time to delete the calendar
                time.sleep(10)
                try:
                    cal = self.checker.principal.calendar(cal_id=cal_id)
                    assert cal
                    cal.events()
                    ## Calendar not deleted, but no exception thrown.
                    ## Perhaps it's a "move to thrashbin"-regime on the server
                    self.feature_checked("delete-calendar", {"support": "unknown", "behaviour": "move to trashbin?"})
                except NotFoundError as e:
                    ## Calendar was deleted, it just took some time.
                    self.feature_checked("delete-calendar", {"support": "fragile", "behaviour": "delayed deletion"})
                    return (calmade, e)
            return (calmade, None)
        except Exception as e:
            self.feature_checked("delete-calendar", False)
            time.sleep(10)
            try:
                cal.delete()
                self.feature_checked("delete-calendar", {"support": "fragile", "behaviour": "deleting a recently created calendar causes exception"})
            except Exception as e2:
                pass
            return (calmade, None)

    def _run_check(self):
        try:
            cal = self.checker.principal.calendar(cal_id="this_should_not_exist")
            cal.events()
            self.feature_checked("create-calendar.auto")
        except (NotFoundError, AuthorizationError): ## robur throws a 403 .. and that's ok
           self.feature_checked("create-calendar.auto", False)
        except Exception as e:
            breakpoint()
            pass

        ## Check on "no_default_calendar" flag
        try:
            cals = self.checker.principal.calendars()
            events = cals[0].events()
            self.feature_checked("get-current-user-principal.has-calendar", True)
        except:
            self.feature_checked("get-current-user-principal.has-calendar", False)

        makeret = self._try_make_calendar(name="Yep", cal_id="pythoncaldav-test")
        if makeret[0]:
            ## calendar created
            ## TODO: this is a lie - we haven't really verified this, only on second script run we will be sure
            self.feature_checked("delete-calendar.free-namespace", True)
            return
        makeret = self._try_make_calendar(cal_id="pythoncaldav-test")
        if makeret[0]:
            self.feature_checked("create-calendar.set-displayname", False)
            self.feature_checked("delete-calendar.free-namespace")
            return
        unique_id1 = "testcalendar-" + str(uuid.uuid4())
        makeret = self._try_make_calendar(cal_id=unique_id1, name="Yep")
        if makeret[0]:
            self.feature_checked("delete-calendar.free-namespace", False)
            return
        unique_id = "testcalendar-" + str(uuid.uuid4())
        makeret = self._try_make_calendar(cal_id=unique_id)
        if makeret[0]:
            self.feature_checked("create-calendar.set-displayname", False)
            self.feature_checked("delete-calendar.free-namespace", False)
            return
        if not "no_mkcalendar" in self.flags_checked:
            self.set_flag("no_mkcalendar", True)

class PrepareCalendar(Check):
    """
    This "check" doesn't check anything, but ensures the calendar has some known events
    """
    features_to_be_checked = set()
    depends_on = { CheckMakeDeleteCalendar }
    features_to_be_checked = { "recurrences.save-load.event", "recurrences.save-load.todo" }
    
    def _run_check(self):

        ## Find or create a calendar
        cal_id = "caldav-server-checker-calendar"
        name = "Calendar for checking server feature support"
        ## TODO: if create-calendar is not supported, then don't do this
        try:
            calendar = self.checker.principal.calendar(cal_id="caldav-server-checker-calendar")
            calendar.events()
        except:
            calendar = self.checker.principal.make_calendar(cal_id=cal_id, name=name)
        self.checker.calendar = calendar

        ## TODO: replace this with one search if possible(?)
        events_from_2000 = calendar.search(event=True, start=datetime(2000,1,1), end=datetime(2001,1,1))
        tasks_from_2000 = calendar.search(todo=True, start=datetime(2000,1,1), end=datetime(2001,1,1))
        ids_existing = [x.component['uid'] for x in events_from_2000 + tasks_from_2000 if datetime(2000,1,1)<x.component.get('DTSTART', datetime(1980,1,1))<datetime(2001,1,1)]

        def add_if_not_existing(*largs, **kwargs):
            if kwargs['uid'] in ids_existing:
                ids_existing.remove(kwargs['uid'])
                return
            return calendar.save_object(*largs, **kwargs)

        recurring_event = add_if_not_existing(
            Event,
            summary="monthly recurring event",
            uid="monthly_recurring_event",
            rrule={'FREQ': 'MONTHLY'},
            dtstart=datetime(2000,1,12,12,0,0)
        )
        recurring_event.load()
        self.feature_checked('recurrences.save-load.event')

        recurring_task = add_if_not_existing(
            Todo,
            summary="monthly recurring task",
            uid="monthly_recurring_event",
            rrule={'FREQ': 'MONTHLY'},
            dtstart=datetime(2000,1,12,12,0,0)
        )
        recurring_task.load()
        self.feature_checked('recurrences.save-load.todo')
        

#class CheckRecurrences(Check):
#    depends_on = { PrepareCalendar }
    
#    def _run_check(self):
        
        

