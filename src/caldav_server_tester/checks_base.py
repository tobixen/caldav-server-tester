from caldav.compatibility_hints import FeatureSet

## WORK IN PROGRESS

## TODO: We need some collector framework that can collect all checks,
## build a dependency graph and mapping from a feature to the relevant
## check.


class Check:
    """
    A "check" may check zero, one or multiple features, as listed in
    caldav.compatibility_hints.FeatureSet.FEATURES.

    A "check" may provision test data for other checks.

    Every check has it's own class.  This is the base class.
    """

    features_checked = set()
    depends_on = set()

    def __init__(self, checker):
        self.checker = checker
        self.client = checker._client_obj

    def set_feature(self, feature, value=True):
        fs = self.checker._features_checked
        if isinstance(value, dict):
            fc = {feature: value}
        elif isinstance(value, str):
            fc = {feature: {"support": value}}
        elif value is True:
            fc = {feature: {"support": "full"}}
        elif value is False:
            fc = {feature: {"support": "unsupported"}}
        elif value is None:
            fc = {feature: {"support": "unknown"}}
        else:
            assert False
        fs.copyFeatureSet(fc, collapse=False)

    def feature_checked(self, feature, return_type=bool):
        return self.checker._features_checked.check_support(feature, return_type)

    def run_check(self, only_once=True):
        if only_once:
            if self.__class__ in self.checker._checks_run:
                return
        for foo in self.depends_on:
            expected_features = self.checker._client_obj.features
            try:
                ## empty feature-set, otherwise different work-arounds may be applied and we'll check nothing
                self.checker._client_obj.features = FeatureSet({})
                foo(self.checker).run_check(only_once=only_once)
            finally:
                self.checker._client_obj.features = expected_features

        ## TODO: record what new features are checked.  Everything in
        ## self.features_checked should be covered, everyhing not in
        ## self.features_checked should not be checked.
        keys_before = set(
            self.checker._features_checked.dotted_feature_set_list().keys()
        )
        self._run_check()

        ## Check that all the declared checking has been done
        keys_after = set(
            self.checker._features_checked.dotted_feature_set_list().keys()
        )
        new_keys = keys_after - keys_before
        missing_keys = self.features_to_be_checked - new_keys
        parent_keys = ()

        ## Missing keys aren't missing if their parents are included.
        ## feature.subfeature.* gets collapsed to feature.subfeature
        missing_keys = set()
        for missing in missing_keys:
            feature_ = missing
            while "." in feature_:
                feature_ = feature_[: feature_.rfind(".")]
                if feature_ in keys_after:
                    missing_keys.remove(missing)
                    parent_keys.add(feature_)
                    break
        assert not missing_keys

        ## Everything checked should be declared
        extra_keys = new_keys - self.features_to_be_checked
        for x in extra_keys:
            for y in parent_keys:
                if x.startswith(y):
                    extra_keys.remove(x)
        assert not extra_keys

        self.checker._checks_run.add(self.__class__)

    def _run_check(self):
        raise NotImplementedError(
            f"A subclass {self.__class__} hasn't implemented the _run_check method"
        )
