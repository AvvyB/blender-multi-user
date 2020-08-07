============
Introduction
============


A film is an idea carved along the whole production process by many different peoples. A traditional animation pipeline involve a linear succession of tasks. From storyboard to compositing by passing upon different step, its fundamental work flow is similar to an industrial assembly line. Since each step is almost a department, its common that one person on department B doesn't know what another person did on a previous step in a department A. This lack of visibility/communication could be a source of problems which could produce a bad impact on the final production result.

.. figure:: img/about_chain.gif
    :align: center

    The linear workflow problems

Nowadays it's a known fact that real-time rendering technologies allows to speedup traditional linear production by reducing drastically the iteration time across different steps. All majors industrial CG solutions are moving toward real-time horizons to bring innovative interactive workflows. But this is a microscopic, per-task/solution vision of real-time rendering benefits for the animation production. What if we step-back, get a macroscopic picture of an animation movie pipeline and ask ourself how real-time could change our global workflow ? Could-it bring better ways of working together by giving more visibility between departments during the whole production ?

The multi-user addon is an attempt to experiment real-time parallelism between different production stage. By replicating blender data blocks over the networks, it allows different artists to collaborate on a same scene in real-time.
