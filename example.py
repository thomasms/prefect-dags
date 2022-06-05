from prefect import Flow, task, Parameter
import hashlib
import string
from random import randint, choices
from typing import Tuple

_hash = lambda x: hashlib.sha256(str(x).encode("utf-8")).hexdigest()


def work_func(text: str, workvalue: str) -> str:
    """The a simple work function"""
    return f"{_hash(text)}{_hash(workvalue)}"


def do_hash(text: str, workvalue: str) -> str:
    return _hash(work_func(text, workvalue))


def check_hash(hashresult: str, difficulty: int) -> bool:
    return int(hashresult, 16) < 2 ** (256 - difficulty)


def do_work(text: str, difficulty: int = 1) -> Tuple[int, str]:
    compare_value = 2 ** (256 - difficulty)

    def check_hash_quick(hashresult: str) -> bool:
        return int(hashresult, 16) < compare_value

    nonce = randint(0, 2**32)
    hashresult = do_hash(text, nonce)
    while check_hash_quick(hashresult) is False:
        nonce += 1
        hashresult = do_hash(text, nonce)
    return (nonce, hashresult)


def verify_work(text: str, workvalue: int, difficulty: int) -> Tuple[bool, str]:
    """workvalue is the cnonce"""
    hashresult = do_hash(text, workvalue)

    return (check_hash(hashresult, difficulty), hashresult)


@task
def generate_random_phrase() -> str:
    N = 16
    return "".join(choices(string.ascii_uppercase + string.digits, k=N))


@task
def get_nonce(text: str, difficulty: int) -> Tuple[int, str]:
    result = do_work(text, difficulty)
    return result


@task
def verify_nonce(text: str, difficulty: int, hash: Tuple[int, str]):
    verified, hashresult = verify_work(text, hash, difficulty)
    if not verified:
        raise RuntimeError(f"Hash is incorrect, got {hashresult}")
    return hashresult


with Flow("pow_flow") as flow:
    difficulty = Parameter("difficulty", default=5)
    random_str = generate_random_phrase()
    nonce, hashresult = get_nonce(random_str, difficulty)
    result = verify_nonce(random_str, difficulty, nonce)

# flow.run(parameters={"difficulty": 17})
flow.visualize()
