from grid2op.Action import TopologyAndDispatchAction
from grid2op.Reward import RedispReward
from grid2op.Rules import DefaultRules
from grid2op.Chronics import Multifolder
from grid2op.Chronics import GridStateFromFile
from grid2op.Backend import PandaPowerBackend

config = {"backend": PandaPowerBackend,
          "action_class": TopologyAndDispatchAction,
          "observation_class": None,
          "reward_class": None,
          "gamerules_class": DefaultRules,
          "chronics_class": Multifolder,
          "grid_value_class": GridStateFromFile,
          "volagecontroler_class": None,
          "thermal_limits": [2000.0,
                             2000.0,
                             2000.0,
                             2000.0,
                             2000.0,
                             2000.0,
                             2000.0,
                             2000.0,
                             4000.0,
                             4000.0,
                             4000.0,
                             4000.0,
                             4000.0,
                             4000.0,
                             4000.0,
                             4000.0,],
          "names_chronics_to_grid": None}