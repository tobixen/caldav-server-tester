## WORK IN PROGRESS

## * One check may check multiple features
## * One "check" may also check no features at all, just provisioning test data for other checks
## * We need a catalogue/dict pointing from feature to check
## * We need a dependency tree, one check may depend that other checks have run

class ServerQuirkChecker:
    """This class will ...

    * Keep the connection details to the server
    * Keep the state of what's already checked

    My idea was to create some clean, nice-looking self-explaining
    code ... but either I'm not qualified for making such code, or the
    problem was more complex than what I assumed.  Perhaps the right
    approach is to just hack on, and then later try to refactor the
    code.

    Having one test for each "quirk", as well as the ability to check
    quirks individually rather than running the full package would be
    nice.  In practice the "quicks" sometimes depend on each other, so
    they have to be run in order.  It's also significant speed
    benefits from not having to rig up and down the calendar for each
    test, and being able to run multiple tests towards the same data
    set.
    """

    def __init__(self, client_obj):
        self.client_obj = client_obj
        self.flags_checked = {}
        self.other_info = {}
        self._default_calendar = None
