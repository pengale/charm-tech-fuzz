#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

from juju import jasyncio
from juju import utils
from juju.controller import Controller
import asyncio
from logging import getLogger
import uuid

LOG = getLogger(__name__)

"""
This is a sketch of a libary to exercise a charm with controller storage.

It utilizes pylibjuju to connect to a controller, make a test model, deploy the charms
under test.

A lot of the code is based on/borrowed from the example code in pylibjuju.


Notes/pseudo code:

# Init

```
        model_name = some_random_id()
        model = model.create()

        try:
                fuzz(model)
                verify(model)
        finally:
                cleanup

```

# Fuzz

```
        parse config file
        run a random set of tests, given a set of routines.

```


# Routines
```

        relate(this, that)
        relate(this, peer)
        unrelate(this, that)
        add_unit(this)
        remove_unit(this)
        apply_config_changes()
```


# Check

Run the verify on everything.
How do we verify? Do we need to dump the contents of some of the saved off objects? Are there facilities for doing this in the OF, or do we need to code them into the charm?
Or can we insert stuff like that automagically into the charm, or do a build that includes a library?

E.g., we copy the charm, write pylibjuju into its requirements, and add a custom testing library to the library? That's not too bad. Can even do that in the OF.

"""

async def main():
    """
    TODO: reshape this to conform w/ plans above.

    """
    controller = Controller()
    print("Connecting to controller")
    # connect to current controller with current user, per Juju CLI
    await controller.connect()

    try:
        model_name = "addmodeltest-{}".format(uuid.uuid4())
        print("Adding model {}".format(model_name))
        model = await controller.add_model(model_name)

        print('Deploying ubuntu')
        application = await model.deploy(
            'cs:ubuntu-10',
            application_name='ubuntu',
            series='trusty',
            channel='stable',
        )

        print('Waiting for active')
        await asyncio.sleep(10)
        await model.block_until(
            lambda: all(unit.workload_status == 'active'
                        for unit in application.units))

        print("Verifying that we can ssh into the created model")
        ret = await utils.execute_process(
            'juju', 'ssh', '-m', model_name, 'ubuntu/0', 'ls /', log=LOG)
        assert ret

        print('Removing ubuntu')
        await application.remove()

        print("Destroying model")
        await controller.destroy_model(model.info.uuid)

    except Exception:
        LOG.exception(
            "Test failed! Model {} may not be cleaned up".format(model_name))

    finally:
        print('Disconnecting from controller')
        if model:
            await model.disconnect()
        await controller.disconnect()


if __name__ == '__main__':
    jasyncio.run(main())
