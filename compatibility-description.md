As of 2025-05, we have a flat list of boolean compatibility flags.  It does not work out very well:

* Sometimes we may want to have other values than only True/False attached to it.
* A hierarchical structure is maybe overkill, but we definitively want to group together some of the values.
* Some of the flags implies other flags.  If `no_xxxfeature` is true, then it's also understood that `no_xxxfeature_on_weird_cornercase` is true.  If all are as simple as this, maybe just have a naming standard that if `no_xxxfeature` is set, it implies `no_xxxfeature*`?
* Sometimes the flags are of a temporary nature and applying only to some specific software package.  Most of the time it's a good idea to follow up with the server developers.
* Missing features should be prepended by `no_`.  But sometimes things are handled gracefully by the server, sometimes server does unexpected things, sometimes things go down in flames, maybe it should be more than just a boolean?
* Extra features should maybe be prepended by `extra_`
* At the very least, the name of the flags should be changed up a bit for consistency

Idea:

Perhaps some of the flags with names starting with `no_` or containing `broken` or `breaks` can be standardized a bit - using name of a feature + cornercases as a key (and name of cornercase may point to another feature), the value can be an enum of how badly unsupported it is, like "unsupported" (handled gracefully, or at least in compliance with the RFC), "fragile" (slightly fragile or non-standard support, may break sometimes, may require workarounds or scaffolding to catch errors on the client side.  This includes rate-limiting), "broken" (results not as expected and in violation of the RFC), "ungraceful" - the server may yield "500 internal server error" or in other ways handle it in such a way that things breaks a lot.  Sometimes this should be followed with a colon and extra explainations.  Sometimes maybe even an extra colon with extra data, like `requests=fragile:rate-limited:5/500s`

Or perhaps it's better to save everything like structured data instead of squeezing too much into the key=value framework.

Here are the flags as of 2025-05-15:

* `rate_limit`: rename to requests=fragile:rate_limited
* `search_delay`: should take a value, and not only boolean.  Rename to search=fragile:delayed-indexing
* `cleanup_calendar`: only test-relevant.  Rename to ... what?
* `no_delete_calendar`: rename to `delete_calendar=unsupported`
* `broken_expand`: rename to `expanded_research=broken`
* `no_expand`: rename to `expanded_research=unsupported`
* `broken_expand_on_exceptions`: rename to `expanded_research_on_recurrence_exception=broken`
* `inaccurate_datesearch`: rename to `date_search=fragile:includes_too_much`
* `no_current-user-principal` - the mixup of underscore/dash is intentional, but it looks ugly.  rename to `current-user-principal=unsupported`
* `no_recurring` - is this related to search, adding events or both?
* `no_recurring_todo` - implicated by `no_recurring`.  is this related to search, adding events or both?
* `no_recurring_todo_expand` - this is an exotic combination.  implicated by both `no_expand` and `no_recurring_todo`.
* `no_scheduling` - rename to `scheduling=unsupported`.
* `no_scehduling_mailbox` - rename to `scheduling_mailbox=unsupported`.
* `no_default_calendar` - rename to `default_calendar=unsupported`.
* `non_existing_calendar_found` - mostly relevant for tests.  Rename to ...what??
* `no_freebusy_rfc4971` - missing feature.  Rename to `freebusy_rfc4971=unsupported`
* `no_freebusy_rfc6638` - missing feature.  Rename to `scheduling_freebusy=unsupported`.
* `calendar_order` - extra feature.  Rename to what??
* `calendar_color` - extra feature.  Rename to what??
* `no_journal` - rename to `journal=unsupported`
* `no_displayname` - rename to `displayname=unsupported`.
* `duplicates_not_allowed` - this is not a missing feature per se.  This is the only that is postfixed with "not allowed".  Perhaps `duplicates=
* `duplicate_in_other_calendar_with_same_uid_is_lost` - a bit related to the previous
* `duplicate_in_other_calendar_with_same_uid_breaks` - maybe breaks can be relaced with `not_allowed`?
* `event_by_url_is_broken` - maybe rename to `no_event_by_uid`?
* `no_delete_event`
* `no_sync_token`
* `time_based_sync_tokens` - so, sligthly broken sync_tokens support
* `fragile_sync_tokens` - so, sligthly broken sync_tokens support
* `sync_breaks_on_delete` - so, sligthly broken sync_tokens support
* `propfind_allpro_failure`

