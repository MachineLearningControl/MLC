import unittest
import MLC.Log.log as lg
import os

from MLC import config as mlc_config_path
from MLC.Common.RandomManager import RandomManager
from MLC.Log.log import set_logger
from MLC.individual.Individual import Individual, OperationOverIndividualFail
from MLC.mlc_parameters.mlc_parameters import Config, saved
from nose.tools import nottest


class IndividualTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        set_logger("testing")

        # Load randoms from file
        cls._random_file = './mlc/unit_matlab_randoms.txt'
        RandomManager.load_random_values(cls._random_file)

        config = Config.get_instance()
        config.read(os.path.join(mlc_config_path.get_test_path(), 'mlc/individual/configuration.ini'))
        Individual._maxdepthfirst = config.getint('GP', 'maxdepthfirst')

        cls._individual_l0 = Individual()
        cls._individual_l0.generate("(root (cos 5.046))")

        cls._individual_l1 = Individual()
        cls._individual_l1.generate("(root (log (sin (exp (tanh 3.6284)))))")

        cls._individual_l2 = Individual()
        cls._individual_l2.generate("(root (cos (* (+ (* -1.912 -9.178) (cos S0)) 3.113)))")

        cls._individual_l3 = Individual()
        cls._individual_l3.generate("(root (log (/ (* (sin 4.37) (- -8.815 -3.902)) (log (+ 2.025 -8.685)))))")

        cls._individual_l4 = Individual()
        cls._individual_l4.generate("(root S0)")

    def setUp(self):
        set_logger("testing")

        # Load randoms from file
        random_file = './mlc/unit_matlab_randoms.txt'
        RandomManager.clear_random_values()
        RandomManager.load_random_values(random_file)

        config = Config.get_instance()
        config.read(os.path.join(mlc_config_path.get_test_path(), 'mlc/individual/configuration.ini'))

        self._individual_l0 = Individual()
        self._individual_l0.generate("(root (cos 5.046))")

        self._individual_l1 = Individual()
        self._individual_l1.generate("(root (log (sin (exp (tanh 3.6284)))))")

        self._individual_l2 = Individual()
        self._individual_l2.generate("(root (cos (* (+ (* -1.912 -9.178) (cos S0)) 3.113)))")

        self._individual_l3 = Individual()
        self._individual_l3.generate("(root (log (/ (* (sin 4.37) (- -8.815 -3.902)) (log (+ 2.025 -8.685)))))")

        self._individual_l4 = Individual()
        self._individual_l4.generate("(root S0)")

    def test_generate_from_value(self):
        individual = Individual()
        individual.generate("(root (exp (tanh (- (tanh -8.049) (* 9.15 -6.848)))))")

        self.assertEquals(individual.get_value(), "(root (exp (tanh (- (tanh -8.049) (* 9.15 -6.848)))))")
        self.assertEquals(individual.get_formal(), "exp(tanh((tanh((-8.049)) - (9.15 .* (-6.848)))))")
        self.assertEquals(individual.get_complexity(), 20)

    def test_random_generate(self):
        individual = Individual()
        individual.generate(individual_type=3)

        self.assertEquals(individual.get_value(), "(root (sin (/ (+ (exp -2.6118) (cos S0)) (/ (log 5.9383) (log -4.5037)))))")
        self.assertEquals(individual.get_formal(), "sin((my_div((exp((-2.6118)) + cos(S0)),(my_div(my_log(5.9383),my_log((-4.5037)))))))")
        self.assertEquals(individual.get_complexity(), 28)

    def test_compare(self):
        individual_1 = Individual()
        individual_1.generate("(root (exp (tanh (- (tanh -8.049) (* 9.15 -6.848)))))")

        individual_2 = Individual()
        individual_2.generate("(root (exp (tanh (- (tanh -8.049) (* 9.15 -6.848)))))")

        self.assertTrue(individual_1.compare(individual_2))

        individual_different = Individual()
        individual_different.generate("(root (cos (+ (sin (log -0.7648)) (exp (tanh 3.6284)))))")

        self.assertFalse(individual_1.compare(individual_different))

    def test_compare_random_individuals(self):
        individual_1 = Individual()
        individual_1.generate(individual_type=3)

        RandomManager.clear_random_values()
        RandomManager.load_random_values(self._random_file)
        individual_2 = Individual()
        individual_2.generate(individual_type=3)

        self.assertTrue(individual_1.compare(individual_2))

    def test_generate_individuals_types(self):
        individual = Individual()

        individual.generate(individual_type=0)
        self._assert_individual(individual, complexity=120,
                                value="(root (sin (+ (/ (cos -3.0973) (exp (log (* (* -1.3423 (tanh (log -3.5094))) (+ (/ (/ (* -9.1213 (cos (exp 3.6199))) (cos (* S0 (cos (- 5.0161 (sin 4.2656)))))) S0) (- (cos (* (+ (sin -9.8591) (exp S0)) -9.4159)) (log (* (- (tanh -8.5969) S0) (/ (exp (/ 8.2118 S0)) (* (* S0 (* 1.6755 -0.0699)) (log (exp -3.2288)))))))))))) S0)))",
                                formal="sin(((my_div(cos((-3.0973)),exp(my_log((((-1.3423) .* tanh(my_log((-3.5094)))) .* ((my_div((my_div(((-9.1213) .* cos(exp(3.6199))),cos((S0 .* cos((5.0161 - sin(4.2656))))))),S0)) + (cos(((sin((-9.8591)) + exp(S0)) .* (-9.4159))) - my_log(((tanh((-8.5969)) - S0) .* (my_div(exp((my_div(8.2118,S0))),((S0 .* (1.6755 .* (-0.0699))) .* my_log(exp((-3.2288))))))))))))))) + S0))")

        individual.generate(individual_type=1)
        self._assert_individual(individual, complexity=24,
                                value="(root (- (sin (* (log -3.7260) (+ -5.0573 -6.2191))) (* 7.3027 (/ (cos S0) (* 4.7410 6.7097)))))",
                                formal="(sin((my_log((-3.7260)) .* ((-5.0573) + (-6.2191)))) - (7.3027 .* (my_div(cos(S0),(4.7410 .* 6.7097)))))")

        individual.generate(individual_type=2)
        self._assert_individual(individual, complexity=15,
                                value="(root (tanh (cos (+ (+ 5.4434 -3.1258) (+ S0 5.1136)))))",
                                formal="tanh(cos(((5.4434 + (-3.1258)) + (S0 + 5.1136))))")

        individual.generate(individual_type=3)
        self._assert_individual(individual, complexity=18,
                                value="(root (log (sin (+ (log -6.2620) (* 8.3709 -6.7676)))))",
                                formal="my_log(sin((my_log((-6.2620)) + (8.3709 .* (-6.7676)))))")

        individual.generate(individual_type=4)
        self._assert_individual(individual, complexity=1,
                                value="(root -0.6212)",
                                formal="(-0.6212)")

    def test_crossover_same_level_0(self):
        individual_1 = Individual()
        individual_1.generate("(root (cos 5.046))")
        individual_2 = Individual()
        individual_2.generate("(root (cos 5.046))")
        new_ind_1, new_ind_2 = individual_1.crossover(individual_2)

        self._assert_individual(new_ind_1, complexity=4,
                                value="(root (cos 5.046))",
                                formal="cos(5.046)")

        self._assert_individual(new_ind_2, complexity=4,
                                value="(root (cos 5.046))",
                                formal="cos(5.046)")

    def test_crossover_same_level_2(self):
        individual_1 = Individual()
        individual_1.generate("(root (cos (* (+ (* -1.912 -9.178) (cos S0)) 3.113)))")
        individual_2 = Individual()
        individual_2.generate("(root (cos (* (+ (* -1.912 -9.178) (cos S0)) 3.113)))")
        new_ind_1, new_ind_2 = individual_1.crossover(individual_2)

        self._assert_individual(new_ind_1, complexity=8,
                                value="(root (cos (* (* -1.912 -9.178) 3.113)))",
                                formal="cos((((-1.912) .* (-9.178)) .* 3.113))")

        self._assert_individual(new_ind_2, complexity=18,
                                value="(root (cos (* (+ (+ (* -1.912 -9.178) (cos S0)) (cos S0)) 3.113)))",
                                formal="cos((((((-1.912) .* (-9.178)) + cos(S0)) + cos(S0)) .* 3.113))")

    def test_crossover_same_level_4(self):
        individual_1 = Individual()
        individual_1.generate("(root S0)")
        individual_2 = Individual()
        individual_2.generate("(root S0)")

        try:
            new_ind_1, new_ind_2 = individual_1.crossover(individual_2)
            self.assertFalse(True, "crossover with individual type 4 should fail")
        except OperationOverIndividualFail, ex:
            self.assertTrue(True)

    def test_crossover_same_individual(self):
        new_ind_1, new_ind_2 = self._individual_l2.crossover(self._individual_l2)

        self._assert_individual(new_ind_1, complexity=8,
                                value="(root (cos (* (* -1.912 -9.178) 3.113)))",
                                formal="cos((((-1.912) .* (-9.178)) .* 3.113))")

        self._assert_individual(new_ind_2, complexity=18,
                                value="(root (cos (* (+ (+ (* -1.912 -9.178) (cos S0)) (cos S0)) 3.113)))",
                                formal="cos((((((-1.912) .* (-9.178)) + cos(S0)) + cos(S0)) .* 3.113))")

    def test_crossover_different_levels_2_3(self):
        # self._engine.rand('seed', 40.0, nargout=0)
        new_ind_1, new_ind_2 = self._individual_l2.crossover(self._individual_l3)

        self._assert_individual(new_ind_1, complexity=8,
                                value="(root (cos (* (- -8.815 -3.902) 3.113)))",
                                formal="cos((((-8.815) - (-3.902)) .* 3.113))")

        self._assert_individual(new_ind_2, complexity=27,
                                value="(root (log (/ (* (sin 4.37) (+ (* -1.912 -9.178) (cos S0))) (log (+ 2.025 -8.685)))))",
                                formal="my_log((my_div((sin(4.37) .* (((-1.912) .* (-9.178)) + cos(S0))),my_log((2.025 + (-8.685))))))")

        # make another to crossover in order to check randomness
        new_ind_1, new_ind_2 = self._individual_l2.crossover(self._individual_l3)

        self._assert_individual(new_ind_1, complexity=8,
                                value="(root (log (+ 2.025 -8.685)))",
                                formal="my_log((2.025 + (-8.685)))")

        self._assert_individual(new_ind_2, complexity=27,
                                value="(root (log (/ (* (sin 4.37) (- -8.815 -3.902)) (cos (* (+ (* -1.912 -9.178) (cos S0)) 3.113)))))",
                                formal="my_log((my_div((sin(4.37) .* ((-8.815) - (-3.902))),cos(((((-1.912) .* (-9.178)) + cos(S0)) .* 3.113)))))")

    def test_crossover_different_levels_0_3(self):
        # self._engine.rand('seed', 40.0, nargout=0)
        new_ind_1, new_ind_2 = self._individual_l0.crossover(self._individual_l3)

        self._assert_individual(new_ind_1, complexity=3,
                                value="(root (- -8.815 -3.902))",
                                formal="((-8.815) - (-3.902))")

        self._assert_individual(new_ind_2, complexity=23,
                                value="(root (log (/ (* (sin 4.37) (cos 5.046)) (log (+ 2.025 -8.685)))))",
                                formal="my_log((my_div((sin(4.37) .* cos(5.046)),my_log((2.025 + (-8.685))))))")

    def test_crossover_different_levels_0_4(self):
        # self._engine.rand('seed', 40.0, nargout=0)
        try:
            new_ind_1, new_ind_2 = self._individual_l0.crossover(self._individual_l4)
            self.assertFalse(True, "crossover with individual type 4 should fail")
        except OperationOverIndividualFail, ex:
            self.assertTrue(True)

    def test_mutate_remove_subtree_and_replace(self):
        # self._engine.rand('seed', 40.0, nargout=0)
        new_ind = self._individual_l3.mutate(Individual.MutationType.REMOVE_SUBTREE_AND_REPLACE)

        self._assert_individual(new_ind, complexity=143,
                                value="(root (log (/ (* (+ (/ (cos -3.0973) (exp (log (* (* -1.3423 (tanh (log -3.5094))) (+ (/ (/ (* -9.1213 (cos (exp S0))) (sin (exp (+ S0 1.7471)))) (- 5.0161 (sin (log S0)))) (- (cos (* (+ (sin S0) 6.2042) S0)) -9.4159)))))) (log (* (- (tanh -8.5969) S0) (/ (exp (/ 8.2118 S0)) (* (* S0 (* (cos (sin (log (exp -3.2288)))) S0)) 0.0290))))) (- -8.815 -3.902)) (log (+ 2.025 -8.685)))))",
                                formal="my_log((my_div((((my_div(cos((-3.0973)),exp(my_log((((-1.3423) .* tanh(my_log((-3.5094)))) .* ((my_div((my_div(((-9.1213) .* cos(exp(S0))),sin(exp((S0 + 1.7471))))),(5.0161 - sin(my_log(S0))))) + (cos(((sin(S0) + 6.2042) .* S0)) - (-9.4159)))))))) + my_log(((tanh((-8.5969)) - S0) .* (my_div(exp((my_div(8.2118,S0))),((S0 .* (cos(sin(my_log(exp((-3.2288))))) .* S0)) .* 0.0290)))))) .* ((-8.815) - (-3.902))),my_log((2.025 + (-8.685))))))")

        # do a second mutation
        new_ind = self._individual_l3.mutate(Individual.MutationType.REMOVE_SUBTREE_AND_REPLACE)

        self._assert_individual(new_ind, complexity=83,
                                value="(root (log (/ (* (sin 4.37) (- -8.815 -3.902)) (tanh (/ (/ -5.0573 (- S0 (/ (cos (log 4.7410)) (exp (/ (log -8.6795) (log (/ (+ 1.4783 (log (+ 2.3213 S0))) (tanh (- (sin 3.7830) (+ -7.5027 3.9792)))))))))) (/ 2.2245 (exp 8.8633)))))))",
                                formal="my_log((my_div((sin(4.37) .* ((-8.815) - (-3.902))),tanh((my_div((my_div((-5.0573),(S0 - (my_div(cos(my_log(4.7410)),exp((my_div(my_log((-8.6795)),my_log((my_div((1.4783 + my_log((2.3213 + S0))),tanh((sin(3.7830) - ((-7.5027) + 3.9792)))))))))))))),(my_div(2.2245,exp(8.8633)))))))))")

    def test_mutate_reparametrization(self):
        # self._engine.rand('seed', 40.0, nargout=0)
        new_ind = self._individual_l3.mutate(Individual.MutationType.REPARAMETRIZATION)

        self._assert_individual(new_ind, complexity=22,
                                value="(root (log (/ (* (sin 0.3271) (- -1.6130 -9.6837)) (log (+ 6.0366 -3.0632)))))",
                                formal="my_log((my_div((sin(0.3271) .* ((-1.6130) - (-9.6837))),my_log((6.0366 + (-3.0632))))))")

        # do a second mutation
        new_ind = self._individual_l3.mutate(Individual.MutationType.REPARAMETRIZATION)

        self._assert_individual(new_ind, complexity=22,
                                value="(root (log (/ (* (sin -2.6118) (- 2.7746 -7.5323)) (log (+ 5.4023 -3.0973)))))",
                                formal="my_log((my_div((sin((-2.6118)) .* (2.7746 - (-7.5323))),my_log((5.4023 + (-3.0973))))))")

    def test_mutate_hoist(self):
        new_ind = self._individual_l3.mutate(Individual.MutationType.HOIST)

        self._assert_individual(new_ind, complexity=17,
                                value="(root (/ (* (sin 4.37) (- -8.815 -3.902)) (log (+ 2.025 -8.685))))",
                                formal="(my_div((sin(4.37) .* ((-8.815) - (-3.902))),my_log((2.025 + (-8.685)))))")

        # do a second mutation
        new_ind = self._individual_l3.mutate(Individual.MutationType.HOIST)

        self._assert_individual(new_ind, complexity=4,
                                value="(root (sin 4.37))",
                                formal="sin(4.37)")

    def test_mutate_shrink(self):
        # self._engine.rand('seed', 40.0, nargout=0)
        new_ind = self._individual_l3.mutate(Individual.MutationType.SHRINK)

        self._assert_individual(new_ind, complexity=19,
                                value="(root (log (/ (* -9.6837 (- -8.815 -3.902)) (log (+ 2.025 -8.685)))))",
                                formal="my_log((my_div(((-9.6837) .* ((-8.815) - (-3.902))),my_log((2.025 + (-8.685))))))")

        # do a second mutation
        new_ind = self._individual_l3.mutate(Individual.MutationType.SHRINK)

        self._assert_individual(new_ind, complexity=15,
                                value="(root (log (/ (* (sin 4.37) (- -8.815 -3.902)) -2.6118)))",
                                formal="my_log((my_div((sin(4.37) .* ((-8.815) - (-3.902))),(-2.6118))))")

    def test_mutate_random_choice(self):
        # mutate random: 4
        new_ind = self._individual_l3.mutate()
        self._assert_individual(new_ind, complexity=8,
                                value="(root (log (+ 2.025 -8.685)))",
                                formal="my_log((2.025 + (-8.685)))")

        # mutate random: 1
        new_ind = self._individual_l3.mutate()
        self._assert_individual(new_ind, complexity=22,
                                value="(root (log (/ (* (sin -2.6118) (- 2.7746 -7.5323)) (log (+ 5.4023 -3.0973)))))",
                                formal="my_log((my_div((sin((-2.6118)) .* (2.7746 - (-7.5323))),my_log((5.4023 + (-3.0973))))))")

        # mutate random: 2
        new_ind = self._individual_l3.mutate()
        self._assert_individual(new_ind, complexity=8,
                                value="(root (log (+ 2.025 -8.685)))",
                                formal="my_log((2.025 + (-8.685)))")

    def test_sensor_list(self):
        # save and restore original configuration
        with saved(Config.get_instance()):
            Config.get_instance().set("POPULATION", "sensor_list", "6,15,2,8,4,10")
            Config.get_instance().set("POPULATION", "sensors", "6")
            Config.get_instance().set("POPULATION", "sensor_spec", "true")
            Config.get_instance().set("POPULATION", "sensor_prob", "1.0")

            # test generate and mutate using sensor list
            individual = Individual()
            individual.generate(individual_type=3)
            self.assertEqual(individual.get_value(), '(root (sin (/ (+ (exp S6) (cos S10)) (/ (log S10) (log S4)))))')

            individual.generate(individual_type=3)
            self.assertEqual(individual.get_value(), '(root (exp (* (- (tanh S6) (tanh S10)) (- (/ S6 S6) (/ S6 S4)))))')

            new_ind = self._individual_l2.mutate(Individual.MutationType.REMOVE_SUBTREE_AND_REPLACE)
            self.assertEqual(individual.get_value(), '(root (exp (* (- (tanh S6) (tanh S10)) (- (/ S6 S6) (/ S6 S4)))))')

            new_ind = self._individual_l2.mutate(Individual.MutationType.REMOVE_SUBTREE_AND_REPLACE)
            self.assertEqual(individual.get_value(), '(root (exp (* (- (tanh S6) (tanh S10)) (- (/ S6 S6) (/ S6 S4)))))')

            new_ind = self._individual_l2.mutate(Individual.MutationType.SHRINK)
            self.assertEqual(individual.get_value(), '(root (exp (* (- (tanh S6) (tanh S10)) (- (/ S6 S6) (/ S6 S4)))))')

            new_ind = self._individual_l2.mutate(Individual.MutationType.SHRINK)
            self.assertEqual(individual.get_value(), '(root (exp (* (- (tanh S6) (tanh S10)) (- (/ S6 S6) (/ S6 S4)))))')

    def test_parameter_controls_generate(self):
        # save and restore original configuration
        with saved(Config.get_instance()):

            # random generation
            Config.get_instance().set("POPULATION", "controls", "3")
            individual = Individual()
            individual.generate(individual_type=2)
            self.assertEqual(individual.get_value(), '(root (/ -3.0632 (cos -3.0973)) (exp (log (* (* S0 -0.8182) (sin -6.5057)))) (/ (/ -1.4169 (/ (* S0 S0) (cos -7.5988))) (log (cos (* S0 5.7489)))))')

            formal_exp = individual.get_formal()
            self.assertIsInstance(formal_exp, list)
            self.assertEqual(len(formal_exp), 3)
            self.assertEqual(formal_exp[0], '(my_div((-3.0632),cos((-3.0973))))')
            self.assertEqual(formal_exp[1], 'exp(my_log(((S0 .* (-0.8182)) .* sin((-6.5057)))))')
            self.assertEqual(formal_exp[2], '(my_div((my_div((-1.4169),(my_div((S0 .* S0),cos((-7.5988)))))),my_log(cos((S0 .* 5.7489)))))')
            self.assertEqual(individual.get_complexity(), 46)

            # generate individual with one control
            Config.get_instance().set("POPULATION", "controls", "1")
            individual = Individual()
            individual.generate("(root (cos (- 5.0161 (sin (log S0)))))")
            self.assertIsInstance(individual.get_formal(), str)
            self.assertEqual(individual.get_formal(), 'cos((5.0161 - sin(my_log(S0))))')
            self.assertEqual(individual.get_complexity(), 14)

            # generate individual with 3 controls
            Config.get_instance().set("POPULATION", "controls", "3")
            individual = Individual()
            individual.generate('(root (exp 2.1314) (* (+ (sin -9.8591) (exp S0)) -9.4159) (exp (/ (/ 8.0187 -8.5969) S0)))')

            formal_exp = individual.get_formal()
            self.assertIsInstance(formal_exp, list)
            self.assertEqual(len(formal_exp), 3)
            self.assertEqual(formal_exp[0], 'exp(2.1314)')
            self.assertEqual(formal_exp[1], '((sin((-9.8591)) + exp(S0)) .* (-9.4159))')
            self.assertEqual(formal_exp[2], 'exp((my_div((my_div(8.0187,(-8.5969))),S0)))')
            self.assertEqual(individual.get_complexity(), 29)

            # generate individual with 5 controls
            Config.get_instance().set("POPULATION", "controls", "5")
            individual = Individual()
            individual.generate('(root (/ (exp (/ 8.2118 S0)) (* (* S0 (* 1.6755 -0.0699)) (log (exp -3.2288)))) S0 0.0290 (* (log (* (+ -5.0573 -6.2191) S0)) (/ (cos (log S0)) (cos (tanh 2.2886)))) (log -8.6795))')

            formal_exp = individual.get_formal()
            self.assertIsInstance(formal_exp, list)
            self.assertEqual(len(formal_exp), 5)
            self.assertEqual(formal_exp[0], '(my_div(exp((my_div(8.2118,S0))),((S0 .* (1.6755 .* (-0.0699))) .* my_log(exp((-3.2288))))))')
            self.assertEqual(formal_exp[1], 'S0')
            self.assertEqual(formal_exp[2], '0.0290')
            self.assertEqual(formal_exp[3], '(my_log((((-5.0573) + (-6.2191)) .* S0)) .* (my_div(cos(my_log(S0)),cos(tanh(2.2886)))))')
            self.assertEqual(formal_exp[4], 'my_log((-8.6795))')
            self.assertEqual(individual.get_complexity(), 64)

            # generate individual with multiple simplifications
            Config.get_instance().set("POPULATION", "controls", "3")
            Config.get_instance().set("OPTIMIZATION", "simplify", "true")
            individual = Individual()
            individual.generate('(root (exp 2.1314) (* (+ (sin -9.8591) (exp S0)) -9.4159) (exp (/ (/ 8.0187 -8.5969) S0)))')

            self.assertEqual(individual.get_value(), "(root 8.4267 (* (+ 0.4208 (exp S0)) -9.4159) (exp (/ -0.9327 S0)))")
            formal_exp = individual.get_formal()
            self.assertIsInstance(formal_exp, list)
            self.assertEqual(len(formal_exp), 3)
            self.assertEqual(formal_exp[0], 'exp(2.1314)')
            self.assertEqual(formal_exp[1], '((sin((-9.8591)) + exp(S0)) .* (-9.4159))')
            self.assertEqual(formal_exp[2], 'exp((my_div((my_div(8.0187,(-8.5969))),S0)))')

    def test_parameter_controls_mutate_hoist(self):
        # save and restore original configuration
        with saved(Config.get_instance()):

            Config.get_instance().set("POPULATION", "controls", "5")
            individual = Individual()
            individual.generate('(root (/ (exp (/ 8.2118 S0)) (* (* S0 (* 1.6755 -0.0699)) (log (exp -3.2288)))) (* (+ (sin -9.8591) (exp S0)) -9.4159) 0.0290 (* (log (* (+ -5.0573 -6.2191) S0)) (/ (cos (log S0)) (cos (tanh 2.2886)))) (log -8.6795))')

            new_ind = individual.mutate(Individual.MutationType.HOIST)
            self.assertEqual(new_ind.get_value(), "(root (log (exp -3.2288)) (* (+ (sin -9.8591) (exp S0)) -9.4159) 0.0290 (* (log (* (+ -5.0573 -6.2191) S0)) (/ (cos (log S0)) (cos (tanh 2.2886)))) (log -8.6795))")

            new_ind = individual.mutate(Individual.MutationType.HOIST)
            self.assertEqual(new_ind.get_value(), "(root (/ (exp (/ 8.2118 S0)) (* (* S0 (* 1.6755 -0.0699)) (log (exp -3.2288)))) (exp S0) 0.0290 (* (log (* (+ -5.0573 -6.2191) S0)) (/ (cos (log S0)) (cos (tanh 2.2886)))) (log -8.6795))")

            new_ind = individual.mutate(Individual.MutationType.HOIST)
            self.assertEqual(new_ind.get_value(), "(root (* S0 (* 1.6755 -0.0699)) (* (+ (sin -9.8591) (exp S0)) -9.4159) 0.0290 (* (log (* (+ -5.0573 -6.2191) S0)) (/ (cos (log S0)) (cos (tanh 2.2886)))) (log -8.6795))")

    def _assert_individual(self, individual, value, formal, complexity):
        self.assertEquals(individual.get_value(), value)
        self.assertEquals(individual.get_formal(), formal)
        self.assertEquals(individual.get_complexity(), complexity)
