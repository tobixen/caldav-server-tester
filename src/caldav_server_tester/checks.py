import time
import uuid
from datetime import timezone
from datetime import datetime
from datetime import date

from caldav.compatibility_hints import FeatureSet
from caldav.lib.error import NotFoundError, AuthorizationError
from caldav.calendarobjectresource import Event, Todo, Journal

from .checks_base import Check

utc = timezone.utc

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

        makeret = self._try_make_calendar(name="Yep", cal_id="caldav-server-checker-mkdel-test")
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
    features_to_be_checked = { "recurrences.save-load.event", "recurrences.save-load.todo", "save-load.event", "save-load.todo", "save-load.todo.mixed-calendar" }
    
    def _run_check(self):
        ## Find or create a calendar
        cal_id = "caldav-server-checker-calendar"
        name = "Calendar for checking server feature support"
        ## TODO: if create-calendar is not supported, then don't do this
        try:
            calendar = self.checker.principal.calendar(cal_id=cal_id)
            calendar.events()
        except:
            calendar = self.checker.principal.make_calendar(cal_id=cal_id, name=name)
        self.checker.calendar = calendar
        self.checker.tasklist = calendar

        ## TODO: replace this with one search if possible(?)
        events_from_2000 = calendar.search(event=True, start=datetime(2000,1,1), end=datetime(2001,1,1))
        tasks_from_2000 = calendar.search(todo=True, start=datetime(2000,1,1), end=datetime(2001,1,1))

        object_by_uid = {}

        self.checker.cnt = 0
        
        for obj in events_from_2000 + tasks_from_2000:
            asdate = lambda foo: foo if type(foo) == date else foo.date()
            component = obj.component
            if 'dtstart' in component and date(2000,1,1) <= asdate(component.start) < date(2001,1,1):
                object_by_uid[obj.component['uid']] = obj

        def add_if_not_existing(*largs, **kwargs):
            self.checker.cnt += 1
            cal = self.checker.tasklist if largs == Todo else self.checker.calendar
            if kwargs.get('uid') in object_by_uid:
                return object_by_uid.pop(kwargs['uid'])
            return cal.save_object(*largs, **kwargs)

        try:
            task_with_dtstart = add_if_not_existing(
                Todo,
                summary="task with a dtstart",
                uid="csc_simple_task1",
                dtstart=date(2000,1,7),
            )
            task_with_dtstart.load()
            self.feature_checked('save-load.todo')
            self.feature_checked('save-load.todo.mixed-calendar')
        except AuthorizationError:
            try:
                tasklist = self.checker.principal.calendar(cal_id=f"{cal_id}_tasks")
                tasklist.todos()
            except:
                tasklist = self.checker.principal.make_calendar(cal_id=cal_id, name=name, supported_calendar_component_set=['VTODO'])
            self.checker.tasklist = tasklist
            task_with_dtstart = add_if_not_existing(
                Todo,
                summary="task with a dtstart",
                uid="csc_simple_task1",
                dtstart=date(2000,1,7),
            )
            task_with_dtstart.load()
            self.feature_checked('save-load.todo.mixed-calendar', False)

        simple_event = add_if_not_existing(
            Event,
            summary="simple event with a start time and an end time",
            uid="csc_simple_event1",
            dtstart=datetime(2000,1,1,12,0,0, tzinfo=utc),
            dtend=datetime(2000,1,1,13,0,0, tzinfo=utc),
        )
        simple_event.load()
        self.feature_checked('save-load.event')

        non_duration_event = add_if_not_existing(
            Event,
            summary="event with a start time but no end time",
            uid="csc_simple_event2",
            dtstart=datetime(2000,1,2,12,0,0, tzinfo=utc),
        )
        
        one_day_event = add_if_not_existing(
            Event,
            summary="event with a start date but no end date",
            uid="csc_simple_event3",
            dtstart=date(2000,1,3),
        )

        two_days_event = add_if_not_existing(
            Event,
            summary="event with a start date and end date",
            uid="csc_simple_event4",
            dtstart=date(2000,1,4),
            dtend=date(2000,1,6),
        )

        task_with_due = add_if_not_existing(
            Todo,
            summary="task with a due date",
            uid="csc_simple_task2",
            due=date(2000,1,8),
        )

        task_with_dtstart_and_due = add_if_not_existing(
            Todo,
            summary="task with a dtstart time and due time",
            uid="csc_simple_task3",
            dtstart=datetime(2000,1,9,12,0,0, tzinfo=utc),
            due=datetime(2000,1,9,13,0,0, tzinfo=utc),
        )

        ## TODO: there are more variants to be tested - dtstart date and due date,
        ## dtstart and duration, only duration, no time spec at all, ...
        
        recurring_event = add_if_not_existing(
            Event,
            summary="monthly recurring event",
            uid="csc_monthly_recurring_event",
            rrule={'FREQ': 'MONTHLY'},
            dtstart=datetime(2000,1,12,12,0,0, tzinfo=utc),
            dtend=datetime(2000,1,12,13,0,0, tzinfo=utc),
        )
        recurring_event.load()
        self.feature_checked('recurrences.save-load.event')

        recurring_task = add_if_not_existing(
            Todo,
            summary="monthly recurring task",
            uid="csc_monthly_recurring_task",
            rrule={'FREQ': 'MONTHLY'},
            dtstart=datetime(2000,1,12,12,0,0, tzinfo=utc),
            due=datetime(2000,1,12,13,0,0, tzinfo=utc),
        )
        recurring_task.load()
        self.feature_checked('recurrences.save-load.todo')

        recurring_event_with_exception = add_if_not_existing(
            Event,
            """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//tobixen//Caldav-Server-Tester//en_DK
BEGIN:VEVENT
UID:csc_monthly_recurring_with_exception
DTSTART:20000113T120000Z
DTEND:20000113T130000Z
DTSTAMP:20240429T181103Z
RRULE:FREQ=MONTHLY
SUMMARY:Monthly recurring with exception
END:VEVENT
BEGIN:VEVENT
UID:csc_monthly_recurring_with_exception
RECURRENCE-ID:20000213T120000Z
DTSTART:20000213T120000Z
DTEND:20000213T130000Z
DTSTAMP:20240429T181103Z
SUMMARY:February recurrence with different summary
END:VEVENT
END:VCALENDAR""")


        ## No more existing IDs in the calendar from 2000 ... otherwise,
        ## more work is needed to ensure those won't pollute the tests nor be
        ## deleted by accident
        assert not object_by_uid
        assert(calendar.events())
        assert(calendar.todos())

class CheckSearch(Check):
    depends_on = { PrepareCalendar }
    features_to_be_checked = { "search.time-range.event", "search.time-range.todo", "search.comp-type-optional" } ## TODO: we can do so much better than this

    def _run_check(self):
        cal = self.checker.calendar
        tasklist = self.checker.tasklist
        events = cal.search(start=datetime(2000,1,1, tzinfo=utc), end=datetime(2000,1,2, tzinfo=utc), event=True)
        self.feature_checked('search.time-range.event', len(events)==1)
        tasks = tasklist.search(start=datetime(2000,1,9, tzinfo=utc), end=datetime(2000,1,10, tzinfo=utc), todo=True, include_completed=True)
        self.feature_checked('search.time-range.todo', len(tasks)==1)
        try:
            objects = cal.search(start=datetime(2000,1,1, tzinfo=utc), end=datetime(2001,1,1, tzinfo=utc))
            if len(objects) == 0:
                self.feature_checked('search.comp-type-optional', {"support": "unsupported", "description": "search that does not include comptype yields nothing"})
            elif cal == tasklist and not any(x for x in objects if isinstance(x, Todo)):
                self.feature_checked('search.comp-type-optional', {"support": "fragile", "description": "search that does not include comptype does not yield tasks"})
            elif len(objects) == self.checker.cnt:
                self.feature_checked('search.comp-type-optional')
            else:
                assert False
        except:
            raise ## TODO: temp temp, handle this better

class CheckRecurrenceSearch(Check):
    depends_on = { CheckSearch }
    features_to_be_checked = {
        "recurrences.search-includes-implicit-recurrences.todo",
        "recurrences.search-includes-implicit-recurrences.event",
        "recurrences.search-includes-implicit-recurrences.infinite-scope",
        "recurrences.expanded-search.todo",
        "recurrences.expanded-search.event",
        "recurrences.expanded-search.exception"
    }
    
    def _run_check(self):
        cal = self.checker.calendar
        events = cal.search(start=datetime(2000,1,12, tzinfo=utc), end=datetime(2000,1,13, tzinfo=utc), event=True)
        assert len(events) == 1
        if self.checker.features_checked.check_support("search.time-range.todo"):
            todos = cal.search(start=datetime(2000,1,12, tzinfo=utc), end=datetime(2000,1,13, tzinfo=utc), todo=True, include_completed=True)
            assert len(todos) == 1
        events = cal.search(start=datetime(2000,2,12, tzinfo=utc), end=datetime(2000,2,13, tzinfo=utc), event=True)
        self.feature_checked('recurrences.search-includes-implicit-recurrences.event', len(events)==1)
        todos = cal.search(start=datetime(2000,2,12, tzinfo=utc), end=datetime(2000,2,13, tzinfo=utc), todo=True)
        self.feature_checked('recurrences.search-includes-implicit-recurrences.todo', len(events)==1)
        
        exception = cal.search(start=datetime(2000,2,13,11, tzinfo=utc), end=datetime(2000,2,13,13, tzinfo=utc), event=True)
        assert len(exception)==1
        far_future_recurrence = cal.search(start=datetime(2045,3,12, tzinfo=utc), end=datetime(2045,3,13, tzinfo=utc), event=True)
        self.feature_checked('recurrences.search-includes-implicit-recurrences.infinite-scope', len(events)==1)

        ## server-side expansion
        events = cal.search(start=datetime(2000,2,12, tzinfo=utc), end=datetime(2000,2,13, tzinfo=utc), event=True, server_expand=True)
        self.feature_checked('recurrences.expanded-search.event', len(events)==1 and events[0].component['dtstart']==datetime(2000,2,12,12,0,0, tzinfo=utc))
        todos = cal.search(start=datetime(2000,2,12, tzinfo=utc), end=datetime(2000,2,13, tzinfo=utc), todo=True, server_expand=True)
        self.feature_checked('recurrences.expanded-search.todo', len(events)==1 and events[0].component['dtstart']==datetime(2000,2,12,12,0,0, tzinfo=utc))
        exception = cal.search(start=datetime(2000,2,13,11, tzinfo=utc), end=datetime(2000,2,13,13, tzinfo=utc), event=True, server_expand=True)
        self.feature_checked('recurrences.expanded-search.exception', len(exception)==1 and exception[0].component['dtstart']==datetime(2000,2,13,12,0,0, tzinfo=utc) and exception[0].component['summary'] == 'February recurrence with different summary')
