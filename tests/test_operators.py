import os

import pytest
from deepdiff import DeepDiff

import bpy
import random


def test_start_session():
    result = bpy.ops.session.host()


    assert 'FINISHED' in result

def test_stop_session():

    result = bpy.ops.session.stop()

    assert 'FINISHED' in result
