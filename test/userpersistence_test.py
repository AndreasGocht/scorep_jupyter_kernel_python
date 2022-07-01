import ast
import inspect
from multiprocessing import shared_memory
import os
import sys
import unittest
import base64
import astunparse
import numpy as np
import pandas as pd
import dill
import uuid
from userpersistence import PersistenceHandler

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import userpersistence


# global variable declaration for load and save variable test
x = 2
y = 3
test_string = "test_string"
window = []


class Testclass():
    z = 4


class_instance = Testclass()
test_list = [1, 2, 3, 4]
df = pd.DataFrame(np.random.randint(0, 100, size=(100, 4)), columns=list('ABCD'))
np_array = np.random.rand(2, 3)


class TestUserpersistence(unittest.TestCase):

    def test_get_user_variables_from_code(self):
        uid = str(uuid.uuid4())
        test_uid = uid
        persistencehandler = PersistenceHandler(test_uid)
        if os.path.isfile("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1.py") and os.path.isfile("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1_target_variables"):
            test_code_file = open("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1.py", "r")
            test_code = test_code_file.read()
            test_code_file.close()
            test_variables_file = open("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1_target_variables", "r")
            test_variables = ast.literal_eval(test_variables_file.read())
            test_variables_file.close()

            variables = persistencehandler.get_user_variables_from_code(test_code)
            # the found variables should contain all the target variables.
            # found variables might contain more variables because they contain also local variables
            # note that local variables are filtered later by merging with globals()
            self.assertTrue(set(test_variables).issubset(variables))

    def test_save_and_load_user_variables(self):
        uid = str(uuid.uuid4())
        test_uid = uid
        persistencehandler = PersistenceHandler(test_uid)
        # declare variables, save them and load them
        # global x, y, test_string, class_instance, test_list, df, np_array, window
        # the functionality to obtain the defined variables by code parsing is tested in
        # test_get_user_variables_from_code()
        variables_from_code = ['x', 'y', 'test_string', 'class_instance', 'test_list', 'df', 'np_array', 'window']
        with open("tmpUserPers.py", "w") as f:
            # create empty file to make things work
            pass
        userpersistence.save_user_variables(globals(), variables_from_code, uid)
        loaded_variables = userpersistence.load_user_variables(uid)
        # now the loaded variables should also occur in globals()
        self.assertTrue(set(globals()).issuperset(loaded_variables))
        persistencehandler.tidy_up()

    def test_save_and_load_user_definitions(self):
        uid = str(uuid.uuid4())
        test_uid = uid
        persistencehandler = PersistenceHandler(test_uid)
        if os.path.isfile("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1.py") and os.path.isfile("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1_target_userdefinitions"):
            test_code_file = open("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1.py", "r")
            test_code = test_code_file.read()
            test_code_file.close()

            persistencehandler.save_user_definitions(test_code, uid)
            

            test_userdefinitions_file = open("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1_target_userdefinitions", "r")
            test_userdefinitions = test_userdefinitions_file.read()
            test_userdefinitions_file.close()

            test_shm_tmp_user_pers = shared_memory.SharedMemory(name='tmp_user_pers_shm_'+uid)
            decoded_res_bytes = base64.b64decode(bytes(test_shm_tmp_user_pers.buf))
            test_userpersistence = dill.loads(decoded_res_bytes)
            self.assertTrue(astunparse.unparse(ast.parse(test_userpersistence)) ==
                            astunparse.unparse(ast.parse(test_userdefinitions)))
            test_shm_tmp_user_pers.close()
            persistencehandler.tidy_up()

    def test_save_and_load_user_definitions_multiple(self):
        uid = str(uuid.uuid4())
        test_uid = uid
        persistencehandler = PersistenceHandler(test_uid)
        if os.path.isfile("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1.py") and os.path.isfile("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1.py") \
                and os.path.isfile("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_2_target_userdefinitions"):
            test_code_file = open("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1.py", "r")
            test_code = test_code_file.read()
            test_code_file.close()
            test_code_file = open("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_2.py", "r")
            test_code2 = test_code_file.read()
            test_code_file.close()
            test_userdefinitions_file = open("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_2_target_userdefinitions", "r")
            test_userdefinitions = test_userdefinitions_file.read()
            test_userdefinitions_file.close()

            persistencehandler.save_user_definitions(test_code, uid)
            persistencehandler.save_user_definitions(test_code2, uid)

            test_shm_tmp_user_pers = shared_memory.SharedMemory(name='tmp_user_pers_shm_' + uid)
            decoded_res_bytes = base64.b64decode(bytes(test_shm_tmp_user_pers.buf))
            test_userpersistence = dill.loads(decoded_res_bytes)

            self.assertTrue(astunparse.unparse(ast.parse(test_userpersistence)) ==
                            astunparse.unparse(ast.parse(test_userdefinitions)))
            test_shm_tmp_user_pers.close()
            persistencehandler.tidy_up()

    def test_save_user_definitions_and_variables(self):
        uid = str(uuid.uuid4())
        test_uid = uid
        persistencehandler = PersistenceHandler(test_uid)
        if os.path.isfile("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1.py") and os.path.isfile("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1_target_userdefinitions"):
            test_code_file = open("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1.py", "r")
            test_code = test_code_file.read()
            test_code_file.close()

            persistencehandler.save_user_definitions(test_code, uid)

            variables_from_code = ['x', 'y', 'test_string', 'class_instance', 'test_list', 'df', 'np_array', 'window']
            userpersistence.save_user_variables(globals(), variables_from_code, uid)
            loaded_variables = userpersistence.load_user_variables(uid)
            # now the loaded variables should also occur in globals()
            self.assertTrue(set(globals()).issuperset(loaded_variables))
            persistencehandler.tidy_up()


    def test_read_shared_memory_vars(self):
        uid = str(uuid.uuid4())
        test_uid = uid
        persistencehandler = PersistenceHandler(test_uid)


        if os.path.isfile("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1.py") and os.path.isfile("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1_target_userdefinitions"):
            test_code_file = open("/home/visitor/Demonstrators/score-p_kernel/scorep_jupyter_kernel_python/test/cases/test_code_1.py", "r")
            test_code = test_code_file.read()
            test_code_file.close()

            persistencehandler.save_user_definitions(test_code, uid)

            variables_from_code = ['x', 'y', 'test_string', 'class_instance', 'test_list', 'df', 'np_array', 'window']
            userpersistence.save_user_variables(globals(), variables_from_code, uid)

            persistencehandler.read_shared_memory_vars(test_uid)
            test_shm_user_vars = shared_memory.SharedMemory(name='tmp_user_vars_shm_' + uid)
            self.assertTrue(persistencehandler.shm_tmp_user_vars.buf == test_shm_user_vars.buf)

            self.assertTrue(dill.loads(base64.b64decode(bytes(persistencehandler.shm_tmp_communication.buf))) == False)
            persistencehandler.tidy_up()


    def test_check_communication_shm(self):
        uid = str(uuid.uuid4())
        test_uid = uid
        persistencehandler = PersistenceHandler(test_uid)

        #shm is on false
        shm_test_bool = persistencehandler.check_communication_shm(test_uid)
        self.assertTrue(shm_test_bool == False)
        

        #shm is on true
        res_bytes = dill.dumps(True)
        output_byte = base64.b64encode(res_bytes)
        persistencehandler.shm_tmp_communication.buf[:len(output_byte)] = output_byte
        
        shm_test_bool = persistencehandler.check_communication_shm(test_uid)
        self.assertTrue(shm_test_bool == True)

    #check attach_and_write_to_shm
    def test_check_attach_and_write_to_shm(self):
        res_bytes = dill.dumps(False)
        output_byte = base64.b64encode(res_bytes)
        test_shm = shared_memory.SharedMemory(name='test_shm', create=True, size=len(output_byte) )

        test_shm.buf[:len(output_byte)] = output_byte
        userpersistence.attach_and_write_to_shm("test_shm")
        test_shm = shared_memory.SharedMemory(name="test_shm")
        self.assertTrue(dill.loads(base64.b64decode(bytes(test_shm.buf))) == True)


if __name__ == '__main__':
    unittest.main()
