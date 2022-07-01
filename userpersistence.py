from glob import glob
import logging
import os
import ast
import astunparse
import dill
from multiprocessing import shared_memory
import base64
from time import sleep

'''
Note: general limitation
changes in modules can not be persisted since pickling/shelving modules is not allowed
this might be fixed by using shared memory
'''



class PersistenceHandler():
    shm_tmp_user_pers = None
    shm_tmp_user_vars = None
    shm_tmp_communication = None


    def __init__(self, uid,  **kwargs):
        res_bytes = dill.dumps(False)
        output_byte = base64.b64encode(res_bytes)
        #decode
        #decoded_res_bytes = base64.b64decode(bytes(shm_tmp_user_vars.buf))
        #decoded_output = dill.loads(decoded_res_bytes)
        #print(decoded_output)

        self.shm_tmp_communication = shared_memory.SharedMemory(name="tmp_communication_shm_"+uid, create=True, size=len(output_byte))
        self.shm_tmp_communication.buf[:len(output_byte)] = output_byte

    def read_shared_memory_vars(self, uid):
        self.shm_tmp_user_vars = shared_memory.SharedMemory(name="tmp_user_vars_shm_"+uid)
        res_bytes = dill.dumps(False)
        output_byte = base64.b64encode(res_bytes)
        self.shm_tmp_communication = shared_memory.SharedMemory(name="tmp_communication_shm_"+uid)
        self.shm_tmp_communication.buf[:len(output_byte)] = output_byte

    def check_communication_shm(self, uid):
       
        if dill.loads(base64.b64decode(bytes(self.shm_tmp_communication.buf))) is not False:
            logging.info("check communication shm succeeded")
            return True
        return False



    #def read_shm_vars(self, uid):
        #self.shm_tmp_user_vars = shared_memory.SharedMemory(name="tmp_user_vars_shm_"+uid)

    
    #tmp_user_pers_file ,must be unique name of tmp_user_pers_shm
    def save_user_definitions(self, code, uid):
        # keep imports, classes and definitions

        root = ast.parse(code)
        code_curr = []
        for top_node in ast.iter_child_nodes(root):
            if isinstance(top_node, ast.With):
                for node in ast.iter_child_nodes(top_node):
                    if (isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef) or
                            isinstance(node, ast.ClassDef) or isinstance(node, ast.Import) or isinstance(node,
                                                                                                        ast.ImportFrom)):
                        code_curr.append(node)
            elif (isinstance(top_node, ast.FunctionDef) or isinstance(top_node, ast.AsyncFunctionDef) or
                isinstance(top_node, ast.ClassDef) or isinstance(top_node, ast.Import) or isinstance(top_node,
                                                                                                    ast.ImportFrom)):
                code_curr.append(top_node)

        code_curr_id = [node.name for node in code_curr if isinstance(node, ast.FunctionDef)
                        or isinstance(node, ast.ClassDef)]


        #get code prev from shared memory (name = tmp_user_pers_shm)
        code_prev = []
        #check if there is a filled shm yet and get prev code from it, decode it
        if self.shm_tmp_user_pers is not None:
            existing_shm_tmp_user_pers = shared_memory.SharedMemory(name='tmp_user_pers_shm_'+uid)
            decoded_res_bytes = base64.b64decode(bytes(existing_shm_tmp_user_pers.buf))
            decoded_output = dill.loads(decoded_res_bytes)
            code_prev = [node for node in ast.iter_child_nodes(ast.parse(decoded_output))]
            #tmp_user_pers_list.extend(code_prev)
            existing_shm_tmp_user_pers.close()
            self.shm_tmp_user_pers.close()
            self.shm_tmp_user_pers.unlink()
            self.shm_tmp_user_pers = None
        # keep info in code prev and close the shm to open new resized shm with same name

        # TODO: use shared memory

        code_to_keep = []
        for node in code_prev:
            # TODO: maintain synch of imports
            # TODO: maintain synch of attributes (del keyword)
            if not (isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef) or
                    isinstance(node, ast.AsyncFunctionDef)):
                code_to_keep.append(node)
            else: 
                if node.name not in code_curr_id:
                    code_to_keep.append(node)
        code_to_keep.append(code_curr)

        tmp_user_pers_shm_string = ""
        for node in code_to_keep:
            tmp_user_pers_shm_string = tmp_user_pers_shm_string + astunparse.unparse(node)

        
        res_bytes = dill.dumps(tmp_user_pers_shm_string)
        output_byte = base64.b64encode(res_bytes)

        self.shm_tmp_user_pers = shared_memory.SharedMemory(name='tmp_user_pers_shm_'+uid, create=True, size=len(output_byte))

        self.shm_tmp_user_pers.buf[:len(output_byte)] = output_byte

        #decode
        #decoded_res_bytes = base64.b64decode(bytes(shm_tmp_user_pers.buf))
        #decoded_output = dill.loads(decoded_res_bytes)
        #tmp_user_pers_string = tmp_user_pers_string + decoded_output


    def get_user_variables_from_code(self, code):
        # found variables might contain more variables because they contain also local variables
        # note that local variables are filtered later by merging with globals()
        root = ast.parse(code)
        # variables = sorted({node.id for node in ast.walk(root) if isinstance(node, ast.Name)})
        variables = set()
        for node in ast.walk(root):
            # assignment nodes can include attributes, therefore go over all targets and check for attribute nodes
            if isinstance(node, ast.Assign) or isinstance(node, ast.AnnAssign):
                for el in node.targets:
                    for target_node in ast.walk(el):
                        if isinstance(target_node, ast.Name):
                            variables.add(target_node.id)

        return variables


    def restore_user_definitions(self, tmp_user_pers_file):
        if os.path.isfile(tmp_user_pers_file):
            os.remove(tmp_user_pers_file)
        if os.path.isfile(tmp_user_pers_file + "_backup"):
            os.rename(tmp_user_pers_file + "_backup", tmp_user_pers_file)




    def tidy_up(self):
        try:
            if self.shm_tmp_user_pers is not None:
                self.shm_tmp_user_pers.close()
                self.shm_tmp_user_pers.unlink()
                self.shm_tmp_user_pers = None
            if self.shm_tmp_user_vars is not None:
                self.shm_tmp_user_vars.close()
                self.shm_tmp_user_vars.unlink()
                self.shm_tmp_user_vars = None
        except:
            print("error tidy up")

#tmp_user_vars_shm
def load_user_variables(uid):
    user_variables = {}
    # TODO: use shared memory
    # get user variables out of shared memory tmp_user_vars_shm not created yet

    try:
        existing_shm_tmp_user_vars = shared_memory.SharedMemory(name='tmp_user_vars_shm_'+uid)
        decoded_res_bytes = base64.b64decode(bytes(existing_shm_tmp_user_vars.buf))
        user_variables = dill.loads(decoded_res_bytes)
        existing_shm_tmp_user_vars.close()
        #shm_tmp_user_vars.close()
        #shm_tmp_user_vars.unlink()
        #shm_tmp_user_vars = None
    except:
        pass

    return user_variables

#tmp_user_pers_shm, tmp_user_vars_shm
def save_user_variables(globs, variables, uid):
    #test if shared memory exists and load from it, decode
    prior_variables = load_user_variables(uid)
    user_variables = {k: v for k, v in globs.items() if str(k) in variables}
    user_variables = {**prior_variables, **user_variables}
    # TODO: use shared memory
    # create tmp_user_vars_shm
    if bool(user_variables):
        res_bytes = dill.dumps(user_variables)
        output_byte = base64.b64encode(res_bytes)

        shm_tmp_user_vars= shared_memory.SharedMemory(name="tmp_user_vars_shm_"+uid ,create=True, size=len(output_byte))
        shm_tmp_user_vars.buf[:len(output_byte)] = output_byte
        return True
    return False
        #decode
        #decoded_res_bytes = base64.b64decode(bytes(shm_tmp_user_vars.buf))
        #decoded_output = dill.loads(decoded_res_bytes)
        #print(decoded_output)

def attach_and_write_to_shm(shm_name):
    res_bytes = dill.dumps(True)
    output_byte = base64.b64encode(res_bytes)
    tmp_shm = shared_memory.SharedMemory(name=shm_name)
    tmp_shm.buf[:len(output_byte)] = output_byte
    sleep(3)