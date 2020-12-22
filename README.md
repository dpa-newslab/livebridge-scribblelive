# livebridge-scribblelive

[![Build Status](https://travis-ci.org/dpa-newslab/livebridge-scribblelive.svg?branch=master)](https://travis-ci.org/dpa-newslab/livebridge-scribblelive)
[![Coverage Status](https://coveralls.io/repos/github/dpa-newslab/livebridge-scribblelive/badge.svg?branch=master)](https://coveralls.io/github/dpa-newslab/livebridge-scribblelive?branch=master)
[![PyPi](https://badge.fury.io/py/livebridge-scribblelive.svg)](https://pypi.python.org/pypi/livebridge-scribblelive)

A [Scribblelive](http://scribblelive.com) plugin for [Livebridge](https://github.com/dpa-newslab/livebridge).

It allows to use a Scribblelive event stream as a target for [Livebridge](https://github.com/dpa-newslab/livebridge).

A converter from Liveblog to Scribblelive is also part of this module.


## Updates in 0.6.1

  - YouTube embeds now use nocookie domain
  - Twutter embeds now use Twitter oembed API to built HTML




## Installation
**Python>=3.5** is needed.
```sh
pip3 install livebridge-scribblelive
```
The plugin will be automatically detected and included from **livebridge** at start time, but it has to be available in **[PYTHONPATH](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH)**

See http://livebridge.readthedocs.io/en/latest/plugins.html#installing-plugins for more infos.

## Plugin specific control file parameters
Under **auth:**
* **user** - scribblelive user
* **password** - scribblelive password
* **api_key** - your scribllelive API key

Under **targets**:
* **type: "scribble"**
* **event_id** -  Id of Scribblelive event.

**Example:**
```
auth:
    scribble:
        user: "email@example.com"
        password: "0123456"
        api_key: "ApIkEy"
bridges:
    - source_id: "1234567890ABDCEF"
      endpoint: "https://example.com/api/"
      type: "demo"
      label: "Example"
      targets:
        - type: "scribble"
          event_id: "12345"
          auth: "scribble"
```

See http://livebridge.readthedocs.io/en/latest/control.html for more infos.

## Testing
**Livebridge** uses [py.test](http://pytest.org/) and [asynctest](http://asynctest.readthedocs.io/) for testing.

Run tests:

```sh
    py.test -v tests/
```

Run tests with test coverage:

```sh
    py.test -v --cov=livebridge_scribblelive --cov-report=html tests/
```

[pytest-cov](https://pypi.python.org/pypi/pytest-cov) has to be installed. In the example above, a html summary of the test coverage is saved in **./htmlcov/**.

## Ideas :

  - remake test skipped in 90a3936a374f5abd6bd0aa1fade018f5c9043f37 

  - https://github.com/aio-libs/async-lru could be used to cache oembed responses from Twitter in livebridge_scribblelive/converters.py 

  - redo instagram? https://developers.facebook.com/docs/instagram/oembed  - contra: does not provide a "do not track" option as of 2020-12-21


## License
Copyright 2016 dpa-infocom GmbH

Apache License, Version 2.0 - see LICENSE for details
