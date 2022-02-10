.. _ways-to-contribute:

##################
Ways to contribute
##################

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
Filing an issue on Gitlab
--------------------------

The `gitlab issue tracker <https://gitlab.com/slumber/multi-user/issues>`_ is used for bug report and enhancement suggestion.
You will need a Gitlab account to be able to open a new issue there and click on "New issue" button in the main multi-user project.

Here are some useful information you should provide in a bug report:

- **Multi-user version**  such as *lastest*, *commit-hash*, *branch*.  This is a must have. Some issues might be relevant in the current stable release, but fixed in the development branch.
- **How to reproduce the bug**. In the majority of cases, bugs are reproducible, i.e. it is possible to trigger them reliably by following some steps. Please always describe those steps as clearly as possible, so that everyone can try to reproduce the issue and confirm it. It could also take the form of a screen capture.

Contributing code
=================

In general, this project follows the `Gitflow Workflow <https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow>`_. It may help to understand that there are three different repositories - the upstream (main multi-user project repository, designated in git by 'upstream'), remote (forked repository, designated in git by 'origin'), and the local repository on your machine.
The following example suggests how to contribute a feature.

1. Fork the project into a new repository:
    https://gitlab.com/yourname/multi-user

2. Clone the new repository locally:
    .. code-block:: bash

        git clone https://gitlab.com/yourname/multi-user.git

3. Keep your fork in sync with the main repository by setting up the upstream pointer once. cd into your git repo and then run:
    .. code-block:: bash
    
        git remote add upstream https://gitlab.com/slumber/multi-user.git

4. Now, locally check out the develop branch, upon which to base your new feature branch:
    .. code-block:: bash

        git checkout develop

5. Fetch any changes from the main upstream repository into your fork (especially if some time has passed since forking):
    .. code-block:: bash

        git fetch upstream
    
    'Fetch' downloads objects and refs from the repository, but doesn’t apply them to the branch we are working on. We want to apply the updates to the branch we will work from, which we checked out in step 4. 

6. Let's merge any recent changes from the remote upstream (original repository's) 'develop' branch into our local 'develop' branch:
    .. code-block:: bash

        git merge upstream/develop

7. Update your forked repository's remote 'develop' branch with the fetched changes, just to keep things tidy. Make sure you haven't committed any local changes in the interim:
    .. code-block:: bash

        git push origin develop

8. Locally create your own new feature branch from the develop branch, using the syntax:
    .. code-block:: bash

        git checkout -b feature/yourfeaturename

    ...where 'feature/' designates a feature branch, and 'yourfeaturename' is a name of your choosing

9. Add and commit your changes, including a commit message:
    .. code-block:: bash

        git commit -am 'Add fooBar'

10. Push committed changes to the remote copy of your new feature branch which will be created in this step:
    
    .. code-block:: bash

        git push -u origin feature/yourfeaturename

    If it's been some time since performing steps 4 through 7, make sure to checkout 'develop' again and pull the latest changes from upstream before checking out and creating feature/yourfeaturename and pushing changes. Alternatively, checkout 'feature/yourfeaturename' and simply run:
    
    .. code-block:: bash

        git rebase upstream/develop

    and your staged commits will be merged along with the changes. More information on `rebasing here <https://git-scm.com/book/en/v2/Git-Branching-Rebasing>`_

.. Hint:: -u option sets up your locally created new branch to follow a remote branch which is now created with the same name on your remote repository.

11. Finally, create a new Pull/Merge Request on Gitlab to merge the remote version of this new branch with commited updates, back into the upstream 'develop' branch, finalising the integration of the new feature.
    Make sure to set the target branch to 'develop' for features and 'master' for hotfixes. Also, include any milestones or labels, and assignees that may be relevant. By default, the Merge option to 'delete source branch when merge request is activated' will be checked.

12. Thanks for contributing!

.. Note:: For hotfixes, replace 'feature/' with 'hotfix/' and base the new branch off the parent 'master' branch instead of 'develop' branch. Make sure to checkout 'master' before running step 8
.. Note:: Let's follow the Atlassian `Gitflow Workflow <https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow>`_, except for one main difference - submitting a pull request rather than merging by ourselves.
.. Note:: See `here <https://philna.sh/blog/2018/08/21/git-commands-to-keep-a-fork-up-to-date/>`_ or `here <https://stefanbauer.me/articles/how-to-keep-your-git-fork-up-to-date>`_ for instructions on how to keep a fork up to date.