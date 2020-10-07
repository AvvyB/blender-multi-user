==================
Ways to contribute
==================

.. Note:: Work in progress 

Testing and reporting issues
============================

A great way of contributing to the multi-user addon is to test development branch and to report issues. 
It is also helpful to report issues discovered in releases, so that they can be fixed in the development branch and in future releases.


----------------------------
Testing development versions
----------------------------

In order to help with the testing, you have several possibilities:

- Test `latest release <https://gitlab.com/slumber/multi-user/-/tags>`_
- Test `development branch <https://gitlab.com/slumber/multi-user/-/branches>`_ 

--------------------------
Filling an issue on Gitlab
--------------------------

The `gitlab issue tracker <https://gitlab.com/slumber/multi-user/issues>`_ is used for bug report and enhancement suggestion.
You will need a Gitlab account to be able to open a new issue there and click on "New issue" button.

Here are some useful information you should provide in a bug report:

- **Multi-user version**  such as *lastest*, *commit-hash*, *branch*.  This is a must have. Some issues might be relevant in the current stable release, but fixed in the development branch.
- **How to reproduce the bug**. In the majority of cases, bugs are reproducible, i.e. it is possible to trigger them reliably by following some steps. Please always describe those steps as clearly as possible, so that everyone can try to reproduce the issue and confirm it. It could also take the form of a screen capture.

Contributing code
=================

1. Fork the project into a new repository: https://gitlab.com/yourname/multi-user
2. Clone the new repository locally:
        .. code-block:: bash
            git clone https://gitlab.com/yourname/multi-user.git
3. Create your own feature branch from the develop branch, using the syntax:
        .. code-block:: bash
            git checkout -b feature/yourfeaturename
    where 'feature/' designates a feature branch, and 'yourfeaturename' is a name of your choosing
4. Pull any recent changes from the 'develop' branch:
        .. code-block:: bash
            git pull
5. Add and commit your changes, including a commit message:
        .. code-block:: bash
            git commit -am 'Add fooBar'
6. Push committed changes to the remote feature branch you created
        .. code-block:: bash
            git push origin feature/yourfeaturename
7. Create a new Pull Request on Gitlab to merge the changes into the develop branch