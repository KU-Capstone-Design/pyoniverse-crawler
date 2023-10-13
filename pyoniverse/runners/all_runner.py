import asyncio
from pathlib import Path

from overrides import override

from pyoniverse.runners.runner import Runner


class AllRunner(Runner):
    @classmethod
    @override
    def run(cls, *args, **kwargs):
        spider_dir = Path("pyoniverse/spiders")
        sub_runners = []
        for spider in spider_dir.glob("*.py"):
            if not spider.name.startswith("__"):
                name = spider.with_suffix("").stem
                cls.logger.info(f"Run {name}")
                sub_runners.append(cls._run(name, *args, **kwargs))
        asyncio.run(cls._collect(sub_runners))

    @classmethod
    async def _collect(cls, sub_runners: list):
        await asyncio.gather(*sub_runners)

    @classmethod
    async def _run(cls, spider: str, *args, **kwargs):
        cmd = f"python main.py --stage={kwargs['stage']} {spider}"
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        cls.logger.info(f"[{cmd} exited with {proc.returncode}]")
        return None
