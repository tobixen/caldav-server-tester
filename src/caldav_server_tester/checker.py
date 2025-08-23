import caldav
import time
import inspect
from caldav.compatibility_hints import FeatureSet

from . import checks
from .checks_base import Check


## TODO: maybe move this to a separate file to resolve dependency problems?
class ServerQuirkChecker:
    """This class will ...

    * Keep the connection details to the server
    * Keep the state of what checks have run
    * Keep the results of all checks that have run
    * Methods for checking all features or a specific feature
    """

    def __init__(self, client_obj):
        self._client_obj = client_obj
        self._features_checked = FeatureSet()
        self._default_calendar = None
        self._checks_run = set()  ## checks that has already been running
        expected_features = self._client_obj.features

    def check_all(self):
        classes = [
            obj
            for name, obj in inspect.getmembers(checks, inspect.isclass)
            if obj.__module__ == checks.__name__
            and issubclass(obj, Check)
            and obj is not Check
        ]
        for cl in classes:
            cl(self).run_check(only_once=True)

    def check_one(self, check_name):
        check = getattr(checks, check_name)(self)
        check.run_check()

    @property
    def features_checked(self):
        return self._features_checked

    def report(self, verbose=False, return_what=str):
        ret = {
            "caldav_version": caldav.__version__,
            "ts": time.time(),
            "name": getattr(self._client_obj, "server_name"),
            "url": str(self._client_obj.url),
            "features": self._features_checked.dotted_feature_set_list(compact=True),
            "error": "Not fully implemnted yet - TODO",
            # "flags_checked": self.flags_checked,
            # "diff1": list(self.diff1),
            # "diff2": list(self.diff2),
        }

        if return_what == "json":
            from json import dumps

            return dumps(ret, indent=4)
        elif return_what == dict:
            return ret
        elif return_what == str:
            raise NotImplementedError(
                "work in progress - can't print out a human-readable report yet"
            )
        else:
            raise NotImplementedError(
                "return types dict, str and 'json' accepted as for now"
            )
