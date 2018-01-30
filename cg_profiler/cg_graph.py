import tensorflow as tf
from tensorflow.python.client import timeline
import json
import os
import pickle
from .cg_operator import Operator

class CompGraph:

    def __init__(self, model_name, run_metadata, tf_graph):

        self.model_name = model_name
        self.run_metadata = run_metadata
        self.tf_graph = tf_graph

        fetched_timeline = timeline.Timeline(self.run_metadata.step_stats)
        chrome_trace = fetched_timeline.generate_chrome_trace_format()

        self.trace_list = json.loads(chrome_trace)

        return

    def get_tensors(self):

        tensor_dict = {}
        self.op_list = []

        for op_trace in self.trace_list['traceEvents']:
            if 'dur' in op_trace.keys():

                op_args = op_trace['args']
                op_name = str(op_args['name'])

                try:
                    tf_repr = self.tf_graph.get_operation_by_name(op_name)

                    op = Operator(op_trace, self.tf_graph, self.model_name)
                    self.op_list.append(op)

                    if not op.is_aid_op:
                        for input_tensor in tf_repr.inputs:
                            tensor_dict[input_tensor.name] = input_tensor
                        for output_tensor in tf_repr.outputs:
                            tensor_dict[output_tensor.name] = output_tensor

                except Exception as excep:
                    # the log should be further redirected to LOG files
                    print(repr(excep))
                    continue

        return tensor_dict

    def op_analysis(self, shape_dict, filename):

        for op in self.op_list:
            op.analysis(shape_dict, self.tf_graph)

        if os.getenv('LOG_OUTPUT_DIR') is not None:
            full_filename = os.path.join(os.getenv('LOG_OUTPUT_DIR'), 'log',
                                         filename)
        else:
            full_filename = os.path.join(os.getenv('HOME'), 'log',
                                         filename)

        with open(full_filename, 'wb') as f:
            pickle.dump(self.op_list, f)

        return

