import dotenv
import pytest

from pyoniverse.out.s3.s3 import S3Sender


@pytest.fixture
def env():
    import os

    while "tests" not in os.listdir():
        os.chdir("..")
    dotenv.load_dotenv()


def test_s3_sender(env):
    # given
    s3_sender = S3Sender()
    # when
    res = s3_sender.send()
    # then
    assert res is True
