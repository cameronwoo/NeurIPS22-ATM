REGISTRY = {}

from .episode_runner import EpisodeRunner
print('REGISTRY 断点1')
REGISTRY["episode"] = EpisodeRunner
print('REGISTRY 断点2')
from .parallel_runner import ParallelRunner
REGISTRY["parallel"] = ParallelRunner
print('REGISTRY 断点3')