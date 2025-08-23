# Improvements to the calendar server compatibility database

I've had a caldav server "quirk"-list in the test directory of the caldav python client library for a long time, but it has become very messy over the time, so I'm going to redo it.

I'm turning from negative language (`no_xxx`, `compatibility_issues`, etc) to positive language (`feature xxx`, `compatibility_hints`, etc).  I'm also changing the design of this "database".

## Old system and experiences

As of 2025-05, we had a flat list of boolean compatibility flags.  Here are some of the problem with the current list:

* Some of the flags implies other flags.  If `no_xxxfeature` is true, then it's also understood that `no_xxxfeature_on_weird_cornercase` is true.
* Missing features was frequently prepended by `no_`.  But sometimes things are handled gracefully by the server, sometimes server does unexpected things, sometimes things go down in flames.  Rather than just a list of boolean flags, it seems like we need at a minimum a key-value store that can hold some information on how well a feature is supported.
* There are differences in the flags.  Some describes client behaviour (like rate limiting) without actually saying anything about the server.  Some describes test behaviour (like how to clean up after running tests).  Some of the flags are indicating extra features that are not part of the RFC - and most flags are indicating problems, things that aren't supported.
* The naming of the flags are quite inconsistent - for instance, the lables sometimes have a dash, other times an underscore to separate words.

## Simple flat dict idea

I did consider to just push the system a bit in the right direction by changing from a list of boolean flags to a key-value-store, thinkking that a full hiearachical database would be overkill.  However, in the end I decided that it wouldn't be future-proof, eventually I would probably overload both the key and the value ... things like `requests=fragile:rate-limited:5/500s` may work, but it's not very nice.

## Structured dict idea

The nice thing with structured dicts is that they may easily be expanded over time, one doesn't need to think up everything from the very start.

Here is what the configuration could look like on a server where we would like to rate-limit requests, where it may take 10 seconds from a change is done until it's reflected in search results, where it's needed to clean up calendar after each test run, where deletion of calendars causes a 500 internal server error, and where expanded search doesn't work.  The latter has been addressed in an issue on the fancypancyserver github:

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
