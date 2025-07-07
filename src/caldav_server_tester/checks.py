from caldav.compatibility_hints import FeatureSet
from .checks_base import Check

## WORK IN PROGRESS

## TODO: We need some collector framework that can collect all checks,
## build a dependency graph and mapping from a feature to the relevant
## check.

class CheckMakeDeleteCalendar(Check):
    """
    Checks (relatively) thoroughly that it's possible to create a calendar and delete it
    """
    features_checked = ['create-calendar', 'delete-calendar']
    depends_on = []

    def _try_make_calendar(self, cal_id, **kwargs):
        """
        Does some attempts on creating and deleting calendars, and sets some
        flags - while others should be set by the caller.
        """
        calmade = False

        ## In case calendar already exists ... wipe it first
        try:
            self.principal.calendar(cal_id=cal_id).delete()
        except:
            pass

        ## create the calendar
        try:
            cal = self.principal.make_calendar(cal_id=cal_id, **kwargs)
            ## calendar creation probably went OK, but we need to be sure...
            cal.events()
            ## calendar creation must have gone OK.
            calmade = True
            self.feature_checked("create-calendar")
            self.set_flag("no_mkcalendar", False)
            self.set_flag("read_only", False)
            self.principal.calendar(cal_id=cal_id).events()
            if kwargs.get("name"):
                try:
                    name = "A calendar with this name should not exist"
                    self.principal.calendar(name=name).events()
                except:
                    ## This is not the exception, this is the normal
                    try:
                        cal2 = self.principal.calendar(name=kwargs["name"])
                        cal2.events()
                        assert cal2.id == cal.id
                        self.set_flag("no_displayname", False)
                    except:
                        self.set_flag("no_displayname", True)

        except Exception as e:
            ## calendar creation created an exception.  Maybe the calendar exists?
            ## in any case, return exception
            cal = self.principal.calendar(cal_id=cal_id)
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
                cal = self.principal.calendar(cal_id=cal_id)
                events = cal.events()
            except NotFoundError:
                cal = None
            ## Delete throw no exceptions, but was the calendar deleted?
            if not cal or (
                self.flags_checked.get(
                    "non_existing_calendar_found" and len(events) == 0
                )
            ):
                self.set_flag("no_delete_calendar", False)
                ## Calendar probably deleted OK.
                ## (in the case of non_existing_calendar_found, we should add
                ## some events t o the calendar, delete the calendar and make
                ## sure no events are found on a new calendar with same ID)
            else:
                ## Calendar not deleted.
                ## Perhaps the server needs some time to delete the calendar
                time.sleep(10)
                try:
                    cal = self.principal.calendar(cal_id=cal_id)
                    assert cal
                    cal.events()
                    ## Calendar not deleted, but no exception thrown.
                    ## Perhaps it's a "move to thrashbin"-regime on the server
                    self.set_flag("no_delete_calendar", "maybe")
                except NotFoundError as e:
                    ## Calendar was deleted, it just took some time.
                    self.set_flag("no_delete_calendar", False)
                    self.set_flag("rate_limited", True)
                    return (calmade, e)
            return (calmade, None)
        except Exception as e:
            self.set_flag("no_delete_calendar", True)
            time.sleep(10)
            try:
                cal.delete()
                self.set_flag("no_delete_calendar", False)
                self.set_flag("rate_limited", True)
            except Exception as e2:
                pass
            return (calmade, None)
