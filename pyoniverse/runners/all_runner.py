import asyncio
from asyncio.subprocess import Process
from pathlib import Path
from typing import Any, Coroutine, List, NoReturn, Sequence

from overrides import override

from pyoniverse.runners.runner import Runner


class AllRunner(Runner):
    @classmethod
    @override
    def run(cls, *args, **kwargs):
        spider_dir = Path("pyoniverse/spiders")
        sub_runners: List[Coroutine[Any, Any, Process]] = []
        for spider in spider_dir.glob("*.py"):
            if not spider.name.startswith("__"):
                name = spider.with_suffix("").stem
                cls.logger.info(f"Run {name}")
                sub_runners.append(
                    asyncio.create_subprocess_exec(
                        "python", "main.py", f"--stage={kwargs['stage']}", name
                    )
                )
        asyncio.run(cls._collect(sub_runners))

    @classmethod
    async def _collect(
        cls, sub_runners: List[Coroutine[Any, Any, Process]]
    ) -> NoReturn:
        subprocesses: Sequence[Process] = await asyncio.gather(*sub_runners)
        for subprocess in subprocesses:
            await subprocess.wait()
