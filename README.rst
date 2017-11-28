==================================
Baluster - Python Composition tool
==================================

.. image:: https://travis-ci.org/palankai/baluster.svg?branch=master
    :target: https://travis-ci.org/palankai/baluster

| Project homepage: `<https://github.com/palankai/baluster>`_
| Issues: `<https://github.com/palankai/baluster/issues>`_
|

What is this package for
------------------------

This package provides a simple way to build back structure of application.
Can be used building composite root as acting a factory for resources,
building a fixture factory for tests.

Features
--------

  - Lazy initialisation
  - Simple composition and dependency handling


Example - composie root
-----------------------

.. code:: python

    from baluster import Baluster, placeholders
    import psycopg2

    class ApplicationRoot(Baluster):
        @placeholders.factory
        def db(self, root):
            # Will be called at the first use
            # Will be cached so won't be called again
            return psycopg2.connect("dbname=test user=postgres")

        @db.close
        def _close_db(self, root, db):
            db.close()

        @placeholders.factory
        def cr(self, root):
            return self.db.cursor()

        @cr.close
        def _close_cr(self, root, cr):
            cr.close()


    def main():
        approot = ApplicationRoot()
        with approot:
            approot.cr.execute('SELECT * FROM user')

        # at this point the connection and the cursor has already been closed


Example - async composie root
-----------------------------

.. code:: python

    from baluster import Baluster, placeholders

    class AsyncApplicationRoot(Baluster):

        @placeholders.factory
        async def resource(self, root):
            # Will be called at the first use
            # Will be cached so won't be called again
            return await some_aync_resource()

        @db.close
        async def _close_resource(self, root, resource):
            await resource.close()


    def main():
        approot = AsyncApplicationRoot()
        async with approot:
            conn = await approot.resource
            await conn.operation(...)

        # at this point the resource has already been closed


Example - fixture factory for tests
-----------------------------------

.. code:: python

    from baluster import Baluster, placeholders
    import psycopg2

    class Fixtures(Baluster):

        @placeholders.factory
        def cr(self, root):
            conn = psycopg2.connect("dbname=test user=postgres")
            return conn.cursor()

        class users(Baluster):

            @placeholders.factory
            def user(self, root):
                root.cr.execute('SELECT * FROM user WHERE id=1')
                return User(root.cr.fetchone())

            @placeholders.factory
            def customer(self, root):
                root.cr.execute('SELECT * FROM customer WHERE id=1')
                return Customer(root.cr.fetchone())

        class orders(Baluster):

            @placeholders.factory
            def amount(self, root):
                return 100

            @placeholders.factory
            def quantity(self, root):
                return 1

            @placeholders.factory
            def order(self, root):
                customer = root.users.customer
                created_by = root.users.user
                amount = self.amount
                # Fictive order object...
                return Order(
                    customer=customer, created_by=created_by,
                    amount=amount, quantity=quantity
                )

            @placeholders.factory
            def shipped_order(self, root):
                order = self.order
                order.mark_shipped()
                return order


    def test_order():
        # Demonstrate a few use fictive usecase

        # Creating order with defaults
        f = Fixtures()
        assert f.order.calculated_total_value == 100
        assert f.order.shipping_address == f.users.customer.address

        # Create new fixtures, but keep some cached data
        f2 = f.copy('cr', 'users')

        # Set some value
        f2.order.amount = 50
        f2.order.quantity = 3
        assert f2.order.calculated_total_value == 150

        # Manage different stage of object life
        f3 = f.copy('cr', 'users')
        order = f3.shipped_order

        with pytest.raises(OrderException):
            order.cancel()
            # as it is shipped


Installation
------------

Python target: >=3.6

.. code::

    $ pip install baluster

Dependencies
------------

The package is independent, using only the python standard library.


Development
-----------

.. code::

   pip install -r requirements-dev.txt

This installs the package in development mode (`setup.py develop`)
and the testing packages.
I would like to achive nearly 100% test coverage.

Test
~~~~
.. code::

   pytest


Contribution
------------

I really welcome any comments!
I would be happy if you fork my code and create pull requests.
For an approved pull request flake8 have to pass just as all of tests.
