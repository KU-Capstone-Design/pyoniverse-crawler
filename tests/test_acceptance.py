import os

import dotenv
import pytest

from pyoniverse.engine import Engine


@pytest.fixture
def env():
    if "tests" not in os.listdir():
        os.chdir("..")
    dotenv.load_dotenv()


@pytest.mark.skip("인수 테스트. 매 배포 시 돌리지 않고 직접 돌린다.")
def test_acceptance(env):
    # given
    engine = Engine(stage="test", spider="all")
    # when
    res = engine.run()
    # then
    assert res is True
