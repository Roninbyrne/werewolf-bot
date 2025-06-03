from Werewolf.core.dir import dirr
from Werewolf.core.git import git
from Werewolf.core.bot import app
from Werewolf.core.bot import start_bot

from .logging import LOGGER

dirr()
git()

__all__ = ["app", "start_bot"]