# caldav-server-tester

**UPDATE 2024-11-18**: I had forgotten completely about this repository.  I'm working on a checker now in the python-caldav library - but it should probably be released as a stand-alone tool.

A planned tool to check how well a caldav server adheres to the caldav standard(s)

Currently there is no code here, this is just sort of a placeholder for a future project.  It is on my todo-list to create this tool, though said list is rather long.

## Existing tools

* The functional test code for the Python CalDAV client library code is catching a lot of issues with the various servers - the problem is that it's not optimized for this purpose - it's just showing that tests are broken, and then it's up to whomever ran the tests to figure out if it's a server side problem or a client side problem.
* I should do some research (or you may issue a pull request) - I believe there already exists some tools like this, but I believe none of them is as thourough as the test code mentioned above

## Background

When creating tests for the python caldav client library, I've realised that the perfect caldav server does not exist - all of them have flaws, almost all of them them breaks with the RFC in different ways - and even if they would technically not break the RFC, there are still many parts of the RFC that are optional, the standards stretches over multiple RFCs, some servers will support only a subset of the RFCs, and there are parts of the RFCs that are ambigious, two servers may behave differently and both may claim they are in compliance with the RFCs.

Eventually I decided to make a list of flags for the tests, allowing parts of the test code to be skipped, or asserts in the test code to be changed depending on those flags.  This did help me run the test code towards multiple different servers.

As time grew and the test code for the caldav library got more and more bloated, the test code got better at finding problems at the server side than on the client side.  I think it's quite useful, the problem is just that the tests are not optimized for this purpose, there are some problems with it:

* The test code will break with some assert or run-time error whenever a server incompatibility is found - but whomever ran the test will have to figure out if it's a client problem or a server problem, figure out what flags to set, and then rerun the tests.  It's a lot of hazzle.
* Setting those flags typically means that the test code will be skipped - if the problems are fixed in some later release of the calendar server, it's needed to manually remove the flag and rerun the tests.  I would like a tool that can alert me when some previously flagged problem has been fixed.
* The test suite does not catch everything.  In particular, the library does have some workarounds to get around some of the server incompatibilities found (like, some servers does not do expansion of recurrent events - now this can be done on the client side in the library, hence the tests will not catch this issue anymore.  There is also code for catching and correcting errors in the icalendar data).

## Ideas for design, usability, implementation, etc

* It should be possible to run it as a stand-alone command-line script.
* It should be able to read connection details both from command-line options, `.config/calendar.conf` (as read by `plann`/`calendar_cli`) as well as `caldav/tests/conf_private.py`
* It should be possible to get the output in json-format
* Output should be compatible with the list in caldav/tests/compatibility_issues.py (but said file may need some editing - and eventually I'd like to move it out of the test directory and make it part of the libary).
* Some of the items in compatibility_issues.py affects the possibility to run tests at all.  In the typical test in the python caldav library I'm creating a calendar, populating it with some known input and then doing queries.  It's needed to be relatively clever so that we can test whatever search queries that can be tested even towards a read-only calendar with arbitrary contents.
