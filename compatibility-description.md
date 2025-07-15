# Improvements to the calendar server compatibility database

I'm turning from negative language (`no_xxx`, `compatibility_issues`, etc) to positive language (`feature xxx`, `compatibility_hints`, etc)

## Current status and experiences

As of 2025-05, we had a flat list of boolean compatibility flags.  It did not work out very well:

* Sometimes we may want to have other values than only True/False attached to it.
* Some of the flags implies other flags.  If `no_xxxfeature` is true, then it's also understood that `no_xxxfeature_on_weird_cornercase` is true.
* Missing features should be prepended by `no_`.  But sometimes things are handled gracefully by the server, sometimes server does unexpected things, sometimes things go down in flames, maybe the level of support needs to be something more than just a boolean flag?
* Some of the flags are indicating extra features that are not part of the RFC.
* The naming of the flags are quite inconsistent - for instance, the lables sometimes have a dash, other times an underscore to separate words.

## Simple flat dict idea

I did consider to just push the system a bit in the right direction by changing from a list of boolean flags to a key-value-store, thinkking that a full hiearachical database would be overkill.  However, in the end I decided that it wouldn't be future-proof and that it would be very ugly as I eventually would hack extra information into both the key and the value.  `requests=fragile:rate-limited:5/500s` may work, but it's not very nice.

## Structured dict idea

The nice thing with structured dicts is that they may easily be expanded over time, one doesn't need to think up everything from the very start.

Here is how configuration could look like on a server where we would like to rate-limit requests, where it may take 10 seconds from a change is done until it's reflected in search results, where it's needed to clean up calendar after each test run, where deletion of calendars causes a 500 internal server error, and where expanded search doesn't work.  The latter has been addressed in an issue on the fancypancyserver github:

```python
fancypancyserver_features = {
    "rate-limit": {
        "enable": True,
        "interval": 100,
        "count": 10,
    },
    "search-cache": {
        "behaviour": "delay",
        "delay": 10
    },
    "tests-cleanup-calendar": {
       "enable": True
    },
    "delete-calendar": {
        "support": "ungraceful"
    },
    "recurrences.expanded-search": {
        "support": "unsupported",
        "links": ["https://github.com/fancy/pancyserver/issues/123"]
    },
    ...
}
```

I decided to make this hierarchically, with `expanded-search` being a child of `recurrences` (but probably `recurrences` should rather be a child of `search` ... hmmm).  The point with such a hierarchy is that it should be possible to just indicate that `recurrences` is not supported, and implicitly it's understood that `recurrences.*.*` is not supported.

Having to create a big nested dict to indicate that feature `foo.blatti.zoo.bar` is not supported would be tedious, so I decided to allow this dotted format.  I'm also considering to make things easier by letting `"recurrences.expanded-search": False` be an easier way to write `"recurrences.expanded-search": { "support": "unsupported" }` and `"recurrences.expanded-search": fragile"` be a shortcut for `"recurrences.expanded-search": { "support": "unsupported" }`.

There should also be a feature definition list.  It may look somehow like this:

```yaml
---
rate-limit:
  type: "client-feature"
  description: >
    client (or test code) must not send requests too fast
  extra-keys:
    interval: "Rate limiting window, in seconds",
    count: "Max number of requests to send within the interval",
  search-cache:
    type: "server-peculiarity",
    description: >
      The server delivers search results from a cache which is not immediately
      updated when an object is changed.  Hence recent changes may not be
      reflected in search results
    extra_keys:
      delay: >
        after this number of seconds, we may be reasonably sure that the
        search results are updated
  tests-cleanup-calendar:
    type: "tests-behaviour",
    description: >
      Deleting a calendar does not delete the objects, or perhaps
      create/delete of calendars does not work at all.  For each test run,
      every calendar resource object should be deleted for every test run
  delete-calendar:
    description: >
      RFC4791 says nothing about deletion of calendars, so the server
      implementation is free to choose weather this should be supported
      or not.  Section 3.2.3.2 in RFC 6638 says that if a calendar is
      deleted, all the calendarobjectresources on the calendar should also
      be deleted - but it's a bit unclear if this only applies to scheduling
      objects or not.  Some calendar servers moves the object to a trashcan
      rather than deleting it
    features:
      free-namespace:
        description: >
          The delete operations clears the namespace, so that another
          calendar with the same ID/name can be created
  recurrences: ## I'm considering to reorganize this into subfeatures of search etc
    description: >
      Support for recurring events and tasks
    features:
      expanded-search:
        description: >
          According to RFC 4791, the server MUST expand recurrence objects
          if asked for it - but many server doesn't do that.  It doesn't
          matter much for the python caldav client project by now, as it does
          the expandation client-side. Some servers don't do expand at all,
          others deliver broken data, typically missing RECURRENCE-ID,
        links:
          - "https://datatracker.ietf.org/doc/html/rfc4791#section-9.6.5"
```

## Discussion points

See https://github.com/tobixen/caldav-server-tester/issues/2
