from nose.tools import nottest
import unittest
import shutil
import os
import MLC.api

from MLC.api.MLCLocal import MLCLocal
from MLC.api.Experiment import Experiment

from MLC.Simulation import Simulation
from MLC.mlc_parameters.mlc_parameters import Config
from MLC.config import set_working_directory
from MLC.Common.RandomManager import RandomManager
from MLC.Log.log import set_logger
from MLC.individual.Individual import Individual as MLCIndividual
from MLC.Population.Population import Population as MLCPopulation
from MLC.db.mlc_repository import IndividualData

import ConfigParser


class MLCWorkspaceTest(unittest.TestCase):
    WORKSPACE_DIR = os.path.abspath("/tmp/mlc_workspace/")
    FILE_WITH_RANDOMS = None
    ORIGINAL_EXPERIMENT = "test_first_experiment"
    ORIGINAL_CONFIGURATION = None
    NEW_EXPERIMENT = "test_new_experiment"
    NEW_CONFIGURATION = None


    @classmethod
    def setUpClass(cls):
        try:
            os.makedirs(MLCWorkspaceTest.WORKSPACE_DIR)
        except OSError:
            shutil.rmtree(MLCWorkspaceTest.WORKSPACE_DIR)
            os.makedirs(MLCWorkspaceTest.WORKSPACE_DIR)

        mlc = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
        # general settings for MLC
        set_logger('console')
        set_working_directory(MLCWorkspaceTest.WORKSPACE_DIR)

        this_dir = os.path.dirname(os.path.abspath(__file__))
        MLCWorkspaceTest.ORIGINAL_CONFIGURATION = \
            os.path.join(this_dir, MLCWorkspaceTest.ORIGINAL_EXPERIMENT + ".conf")
        MLCWorkspaceTest.NEW_CONFIGURATION = \
            os.path.join(this_dir, MLCWorkspaceTest.NEW_EXPERIMENT + ".conf")
        mlc.new_experiment(MLCWorkspaceTest.ORIGINAL_EXPERIMENT,
                           MLCWorkspaceTest.ORIGINAL_CONFIGURATION)

        # random file for simulations
        MLCWorkspaceTest.FILE_WITH_RANDOMS = os.path.join(this_dir, "matlab_randoms.txt")

    @classmethod
    def teardownClass(cls):
        shutil.rmtree(MLCWorkspaceTest.WORKSPACE_DIR)

    def test_obtain_experiments(self):
        mlc = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
        experiments = mlc.get_workspace_experiments()
        self.assertEqual(len(experiments), 1)
        self.assertEqual(experiments[0], MLCWorkspaceTest.ORIGINAL_EXPERIMENT)

    def test_obtain_configuration_from_a_closed_experiment(self):
        try:
            mlc = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
            mlc.get_experiment_configuration(MLCWorkspaceTest.ORIGINAL_EXPERIMENT)
            self.assertTrue(False, "Configuration from a closed experiment should not be obtained")
        except MLC.api.mlc.ClosedExperimentException:
            self.assertTrue(True)

    def test_open_invalid_experiment(self):
        try:
            mlc = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
            mlc.open_experiment("invalid_name")
            self.assertTrue(False)
        except MLC.api.mlc.ExperimentNotExistException:
            self.assertTrue(True)

    def test_obtain_configuration(self):
        mlc = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
        mlc.open_experiment(MLCWorkspaceTest.ORIGINAL_EXPERIMENT)
        configuration = mlc.get_experiment_configuration(MLCWorkspaceTest.ORIGINAL_EXPERIMENT)

        # check configuration structure
        self.assertIsInstance(configuration, dict)
        self.assertTrue(configuration.has_key("BEHAVIOUR"))
        self.assertIsInstance(configuration["BEHAVIOUR"], dict)
        self.assertTrue(configuration["BEHAVIOUR"].has_key("showeveryitbest"))
        self.assertEqual(configuration["BEHAVIOUR"]["showeveryitbest"], "true")

    def test_open_and_close_experiment(self):
        mlc = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
        mlc.open_experiment(MLCWorkspaceTest.ORIGINAL_EXPERIMENT)
        mlc.close_experiment(MLCWorkspaceTest.ORIGINAL_EXPERIMENT)
        try:
            mlc.get_experiment_configuration(MLCWorkspaceTest.ORIGINAL_EXPERIMENT)
            self.assertTrue(False, "Configuration from a closed experiment should not be obtained")
        except MLC.api.mlc.ClosedExperimentException:
            self.assertTrue(True)

    def test_create_duplicated_experiment(self):
        try:
            mlc = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
            mlc.new_experiment(MLCWorkspaceTest.ORIGINAL_EXPERIMENT,
                               MLCWorkspaceTest.ORIGINAL_CONFIGURATION)
            self.assertTrue(False)
        except MLC.api.mlc.DuplicatedExperimentError:
            self.assertTrue(True)

    def test_create_experiment_and_obtain_configuration(self):
        try:
            mlc = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
            mlc.new_experiment(MLCWorkspaceTest.NEW_EXPERIMENT,
                               MLCWorkspaceTest.NEW_CONFIGURATION)
            mlc.open_experiment(MLCWorkspaceTest.NEW_EXPERIMENT)
            configuration = mlc.get_experiment_configuration(MLCWorkspaceTest.NEW_EXPERIMENT)
            print configuration
            mlc.close_experiment(MLCWorkspaceTest.NEW_EXPERIMENT)

            # check configuration structure
            self.assertIsInstance(configuration, dict)
            self.assertTrue(configuration.has_key("PARAMS"))
            self.assertIsInstance(configuration["PARAMS"], dict)
            self.assertTrue(configuration["PARAMS"].has_key("test_param"))
            self.assertEqual(configuration["PARAMS"]["test_param"], "test_value")

        finally:
            # FIXME: use Setup/TearDown testcase
            mlc.delete_experiment(MLCWorkspaceTest.NEW_EXPERIMENT)

    def test_delete_experiment(self):
        # delete an experiment that not exists
        try:
            mlc = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
            mlc.delete_experiment(MLCWorkspaceTest.NEW_EXPERIMENT)
            self.assertTrue(False)
        except MLC.api.mlc.ExperimentNotExistException:
            self.assertTrue(True)

        mlc.new_experiment(MLCWorkspaceTest.NEW_EXPERIMENT,
                           MLCWorkspaceTest.NEW_CONFIGURATION)
        mlc.delete_experiment(MLCWorkspaceTest.NEW_EXPERIMENT)
        self.assertFalse(os.path.exists(os.path.join(MLCWorkspaceTest.WORKSPACE_DIR,
                                                     MLCWorkspaceTest.NEW_EXPERIMENT)))

    def test_set_configuration(self):
        try:
            mlc = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)

            # check original configuration
            mlc.new_experiment(MLCWorkspaceTest.NEW_EXPERIMENT, MLCWorkspaceTest.NEW_CONFIGURATION)
            mlc.open_experiment(MLCWorkspaceTest.NEW_EXPERIMENT)
            original_config = mlc.get_experiment_configuration(MLCWorkspaceTest.NEW_EXPERIMENT)
            self.assertEqual(original_config["PARAMS"]["test_param"], "test_value")
            # chage paramenter value
            mlc.set_experiment_configuration(MLCWorkspaceTest.NEW_EXPERIMENT, {"PARAMS": {"test_param": "new_value"}})
            mlc.close_experiment(MLCWorkspaceTest.NEW_EXPERIMENT)

            # reload mlc_workspace
            mlc_reloaded = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
            mlc_reloaded.open_experiment(MLCWorkspaceTest.NEW_EXPERIMENT)
            original_config = mlc_reloaded.get_experiment_configuration(MLCWorkspaceTest.NEW_EXPERIMENT)
            self.assertEqual(original_config["PARAMS"]["test_param"], "new_value")
            mlc_reloaded.close_experiment(MLCWorkspaceTest.NEW_EXPERIMENT)

            # set specific parameter
            mlc = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
            mlc.open_experiment(MLCWorkspaceTest.NEW_EXPERIMENT)
            mlc.set_experiment_configuration_parameter(MLCWorkspaceTest.NEW_EXPERIMENT,
                                                       "another_section", "another_param",
                                                       "another_value")
            mlc.close_experiment(MLCWorkspaceTest.NEW_EXPERIMENT)

            # reload mlc_workspace
            mlc_reloaded = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
            mlc_reloaded.open_experiment(MLCWorkspaceTest.NEW_EXPERIMENT)
            config = mlc_reloaded.get_experiment_configuration(MLCWorkspaceTest.NEW_EXPERIMENT)
            mlc_reloaded.close_experiment(MLCWorkspaceTest.NEW_EXPERIMENT)
            self.assertEqual(config["PARAMS"]["test_param"], "new_value")

            self.assertIn("another_section", config)
            self.assertIn("another_param", config["another_section"])
            self.assertEqual(config["another_section"]["another_param"], "another_value")

        finally:
            # FIXME: use Setup/TearDown testcase
            mlc.delete_experiment(MLCWorkspaceTest.NEW_EXPERIMENT)
            pass

    def test_get_info_empty_simulation(self):
        mlc = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
        mlc.open_experiment(MLCWorkspaceTest.ORIGINAL_EXPERIMENT)
        info = mlc.get_experiment_info(MLCWorkspaceTest.ORIGINAL_EXPERIMENT)

        self._assert_key_value(info, "name", MLCWorkspaceTest.ORIGINAL_EXPERIMENT)
        self._assert_key_value(info, "filename", MLCWorkspaceTest.ORIGINAL_EXPERIMENT + ".mlc")
        self._assert_key_value(info, "generations", 0)
        self._assert_key_value(info, "individuals", 0)
        self._assert_key_value(info, "individuals_per_generation", 10)

        mlc.close_experiment(MLCWorkspaceTest.ORIGINAL_EXPERIMENT)

    @nottest
    def test_go_and_check_simulation_info(self):
        try:
            # load random values for the simulation
            self._load_random_values()

            # Execute a simulation
            mlc = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
            mlc.new_experiment("test_go_and_check", MLCWorkspaceTest.ORIGINAL_CONFIGURATION)
            mlc.open_experiment("test_go_and_check")
            mlc.go("test_go_and_check", 2)

            # check simulation info
            info = mlc.get_experiment_info("test_go_and_check")
            self._assert_key_value(info, "name", "test_go_and_check")
            self._assert_key_value(info, "filename", "test_go_and_check" + ".mlc")
            self._assert_key_value(info, "generations", 2)
            self._assert_key_value(info, "individuals", 11)
            self._assert_key_value(info, "individuals_per_generation", 10)

        finally:
            # FIXME: use Setup/TearDown testcase
            os.unlink(os.path.join(MLCWorkspaceTest.WORKSPACE_DIR, "test_go_and_check") + ".conf")
            os.unlink(os.path.join(MLCWorkspaceTest.WORKSPACE_DIR, "test_go_and_check") + ".mlc")
            pass

    def test_go_and_get_individuals(self):
        try:
            # load random values for the simulation
            self._load_random_values()

            # Execute a simulation
            mlc = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
            mlc.new_experiment("test_go_and_check", MLCWorkspaceTest.ORIGINAL_CONFIGURATION)
            mlc.open_experiment("test_go_and_check")
            mlc.go("test_go_and_check", 2)

            # obtain individuals
            individuals = mlc.get_individuals("test_go_and_check")

            # check number of individuals
            self.assertEqual(len(individuals), 11)

            # TODO: Check individual values
            for indiv_id, indiv_data in individuals.items():
                self.assertIsInstance(indiv_data, IndividualData)

            # Test Update Individual Cost in all generations
            mlc.update_individual_cost("test_go_and_check", 2, 1000, 1001)

            indiv_data = mlc.get_individuals("test_go_and_check")[2]
            self.assertEqual(indiv_data.get_appearances(), 2)
            self.assertEqual(indiv_data.get_cost_history(), {1: [(1000.0, 1001)], 2: [(1000.0, 1001)]})
            mlc.close_experiment("test_go_and_check")
        finally:
            # FIXME: use Setup/TearDown testcase
            mlc.delete_experiment("test_go_and_check")

    @nottest
    def test_go_and_get_generations(self):
        try:
                # load random values for the simulation
            self._load_random_values()

            # Execute a simulation
            mlc = MLCLocal(working_dir=MLCWorkspaceTest.WORKSPACE_DIR)
            mlc.new_experiment("test_go_and_check", MLCWorkspaceTest.ORIGINAL_CONFIGURATION)
            mlc.open_experiment("test_go_and_check")
            mlc.go("test_go_and_check", 2)

            # get first population
            first_generation = mlc.get_generation("test_go_and_check", 1)
            self.assertIsInstance(first_generation, MLCPopulation)

            # get second generation
            second_generation = mlc.get_generation("test_go_and_check", 2)
            self.assertIsInstance(second_generation, MLCPopulation)

            # third generation does not exist and must raise an Exception
            # TODO: Use a specific exception instead of IndexError

            try:
                third_generation = mlc.get_generation("test_go_and_check", 3)
                self.assertIsInstance(third_generation, MLCPopulation)
                self.assertTrue(False)
            except IndexError:
                self.assertTrue(True)

        finally:
            # FIXME: use Setup/TearDown testcase
            os.unlink(os.path.join(MLCWorkspaceTest.WORKSPACE_DIR, "test_go_and_check") + ".conf")
            os.unlink(os.path.join(MLCWorkspaceTest.WORKSPACE_DIR, "test_go_and_check") + ".mlc")
            pass

    def _assert_key_value(self, dictionary, key, value):
        self.assertIsInstance(dictionary, dict)
        self.assertIn(key, dictionary)
        self.assertEqual(dictionary[key], value)

    def _load_random_values(self):
        RandomManager.clear_random_values()
        RandomManager.load_random_values(MLCWorkspaceTest.FILE_WITH_RANDOMS)
